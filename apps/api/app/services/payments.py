from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import logging
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from urllib.parse import urlencode
from uuid import UUID, uuid4

import httpx
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.individual_lessons import (
    IndividualLessonOffer,
    LessonBooking,
    LessonPackage,
    LessonPackageStatus,
    LessonSlot,
    LessonSlotStatus,
)
from app.models.payments import (
    PaymentProvider,
    PromoCode,
    PurchaseOrder,
    PurchaseOrderStatus,
)
from app.models.user import User
from app.services import individual_lessons as lessons

logger = logging.getLogger(__name__)

# Сколько максимум держим слот за неоплаченным заказом, если ЮKassa всё ещё
# показывает платёж в процессе. Дальше платёж отменяем и слот освобождаем.
MAX_PAYMENT_RESERVATION_HOURS = 24
EXPIRED_ORDERS_BATCH = 20

# Официальный список адресов, с которых ЮKassa присылает HTTP-уведомления.
YOOKASSA_WEBHOOK_NETWORKS = tuple(
    ipaddress.ip_network(value)
    for value in (
        "185.71.76.0/27",
        "185.71.77.0/27",
        "77.75.153.0/25",
        "77.75.156.11/32",
        "77.75.156.35/32",
        "77.75.154.128/25",
        "2a02:5180::/32",
    )
)


class PaymentError(Exception):
    pass


class PromoCodeError(Exception):
    pass


class PriceNotSetError(PaymentError):
    pass


def discount_amounts(price_minor: int, percent: Decimal) -> tuple[int, int]:
    """Скидка в копейках с округлением до рубля и итоговая сумма."""
    discount_minor = (
        (Decimal(price_minor) * percent / Decimal(100) / Decimal(100))
        .quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        * 100
    )
    discount_minor = min(int(discount_minor), price_minor)
    return discount_minor, price_minor - discount_minor


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def is_yookassa_webhook_ip(value: str | None) -> bool:
    """Проверяем последний адрес цепочки: его добавил доверенный nginx."""
    if not value:
        return False
    address = value.split(",")[-1].strip()
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return any(ip in network for network in YOOKASSA_WEBHOOK_NETWORKS)


def _prodamus_normalize(value: object) -> object:
    if isinstance(value, dict):
        return {
            str(key): _prodamus_normalize(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_prodamus_normalize(item) for item in value]
    return str(value)


def prodamus_signature(values: dict, secret_key: str) -> str:
    """Подпись Prodamus: отсортированный JSON + HMAC-SHA256."""
    payload = json.dumps(
        _prodamus_normalize(values),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hmac.new(
        secret_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def verify_prodamus_signature(values: dict, signature: str | None, secret_key: str) -> bool:
    if not secret_key or not signature:
        return False
    expected = prodamus_signature(values, secret_key)
    return hmac.compare_digest(expected, signature.strip().lower())


def _prodamus_payment_url(
    order: PurchaseOrder, offer: IndividualLessonOffer, user: User, settings
) -> str:
    amount = f"{Decimal(order.total_minor) / Decimal(100):.2f}"
    data = {
        "do": "pay",
        "callbackType": "json",
        "order_id": str(order.id),
        "customer_email": user.email,
        "payment_method": settings.prodamus_payment_method,
        "currency": settings.prodamus_currency,
        "products": [
            {
                "name": f"Индивидуальный урок: {offer.title}",
                "sku": str(offer.id),
                "price": amount,
                "quantity": "1",
            }
        ],
    }
    params = {
        key: str(value)
        for key, value in data.items()
        if key not in {"products"}
    }
    for index, product in enumerate(data["products"]):
        for key, value in product.items():
            params[f"products[{index}][{key}]"] = str(value)
    params["signature"] = prodamus_signature(data, settings.prodamus_secret_key)
    return f"{settings.prodamus_form_url.rstrip('/')}/?{urlencode(params)}"


async def _yookassa(
    method: str,
    path: str,
    *,
    body: dict | None = None,
    idempotence_key: str | None = None,
) -> dict:
    settings = get_settings()
    if not settings.yookassa_shop_id or not settings.yookassa_secret_key:
        raise PaymentError("ЮKassa не настроена")

    headers = {"Idempotence-Key": idempotence_key} if idempotence_key else {}
    async with httpx.AsyncClient(
        base_url=settings.yookassa_api_url,
        auth=(settings.yookassa_shop_id, settings.yookassa_secret_key),
        headers=headers,
        timeout=15,
    ) as client:
        response = await client.request(method, path, json=body)

    if response.status_code >= 400:
        raise PaymentError(f"ЮKassa вернула ошибку: {response.status_code}")
    return response.json()


async def _release_promo_reservation(
    session: AsyncSession, order: PurchaseOrder
) -> None:
    if order.promo_code_id is None:
        return

    promo = await session.scalar(
        select(PromoCode)
        .where(PromoCode.id == order.promo_code_id)
        .with_for_update()
    )
    if promo is not None and promo.reserved_order_id == order.id:
        promo.reserved_order_id = None


async def _release_slot(session: AsyncSession, order: PurchaseOrder) -> None:
    slot = await session.scalar(
        select(LessonSlot)
        .where(
            LessonSlot.id == order.slot_id,
            LessonSlot.status == LessonSlotStatus.BLOCKED.value,
        )
        .with_for_update()
    )
    if slot is None:
        return

    other_order = await session.scalar(
        select(PurchaseOrder.id).where(
            PurchaseOrder.slot_id == order.slot_id,
            PurchaseOrder.id != order.id,
            PurchaseOrder.status == PurchaseOrderStatus.PENDING.value,
        )
    )
    booking = await session.scalar(
        select(LessonBooking.id).where(LessonBooking.slot_id == order.slot_id)
    )
    if other_order is None and booking is None:
        slot.status = LessonSlotStatus.FREE.value


async def _expire_order(session: AsyncSession, order: PurchaseOrder) -> None:
    order.status = PurchaseOrderStatus.EXPIRED.value
    await _release_promo_reservation(session, order)
    await _release_slot(session, order)


def _assert_yookassa_payment(order: PurchaseOrder, payment: dict) -> None:
    amount = payment.get("amount") or {}
    value = amount.get("value")
    if not isinstance(value, str):
        raise PaymentError("ЮKassa не вернула сумму платежа")
    if Decimal(value) != Decimal(order.total_minor) / Decimal(100):
        raise PaymentError("Сумма платежа не совпадает с заказом")
    if (payment.get("metadata") or {}).get("order_id") != str(order.id):
        raise PaymentError("Платёж не соответствует заказу")


def _assert_prodamus_payment(order: PurchaseOrder, values: dict) -> None:
    if values.get("order_num") != str(order.id):
        raise PaymentError("Уведомление не соответствует заказу")
    if str(values.get("currency", "")).lower() != order.currency.lower():
        raise PaymentError("Валюта платежа не совпадает с заказом")
    try:
        amount = Decimal(str(values["sum"])).quantize(Decimal("0.01"))
    except (KeyError, ValueError, ArithmeticError) as exc:
        raise PaymentError("Prodamus не вернул сумму платежа") from exc
    if amount != Decimal(order.total_minor) / Decimal(100):
        raise PaymentError("Сумма платежа не совпадает с заказом")


async def _apply_paid_order(session: AsyncSession, order: PurchaseOrder) -> None:
    user = await session.get(User, order.user_id)
    if user is None:
        raise PaymentError("Пользователь заказа не найден")

    now = datetime.now(UTC)
    offer = order.offer
    slot = await session.scalar(
        select(LessonSlot).where(LessonSlot.id == order.slot_id).with_for_update()
    )
    other_pending = await session.scalar(
        select(PurchaseOrder.id).where(
            PurchaseOrder.slot_id == order.slot_id,
            PurchaseOrder.id != order.id,
            PurchaseOrder.status == PurchaseOrderStatus.PENDING.value,
        )
    )

    can_book = (
        slot is not None
        and other_pending is None
        and slot.status
        in {LessonSlotStatus.FREE.value, LessonSlotStatus.BLOCKED.value}
        and _as_utc(slot.starts_at) > now
        and slot.duration_minutes == offer.duration_minutes
    )
    if can_book:
        booked_days = await lessons.booked_day_keys(session, user)
        day_key = lessons.local_day_key(slot.starts_at, lessons.user_timezone(user))
        can_book = day_key not in booked_days

    package = LessonPackage(
        user_id=user.id,
        offer_id=offer.id,
        total_lessons=offer.lessons_count,
        remaining_lessons=offer.lessons_count,
        status=LessonPackageStatus.ACTIVE.value,
        expires_at=(
            now + timedelta(days=offer.validity_days) if offer.validity_days else None
        ),
    )
    session.add(package)
    await session.flush()
    await session.refresh(package, attribute_names=["offer"])

    if can_book:
        await lessons._create_booking(session, user, package, slot)
    else:
        # Деньги списаны, но выбранный слот уже занят или прошёл. Не теряем
        # оплату: занятие остаётся в пакете, ученик выберет новое время.
        logger.warning(
            "Заказ %s оплачен, но слот %s недоступен; занятие осталось в пакете",
            order.id,
            order.slot_id,
        )
        if slot is not None:
            await _release_slot(session, order)

    if order.promo_code_id is not None:
        promo = await session.scalar(
            select(PromoCode)
            .where(PromoCode.id == order.promo_code_id)
            .with_for_update()
        )
        if promo is not None:
            if promo.used_at is None:
                promo.used_at = now
            promo.reserved_order_id = None

    order.status = PurchaseOrderStatus.SUCCEEDED.value


async def release_expired_orders(session: AsyncSession) -> None:
    now = datetime.now(UTC)
    orders = (
        await session.scalars(
            select(PurchaseOrder)
            .where(
                PurchaseOrder.status == PurchaseOrderStatus.PENDING.value,
                PurchaseOrder.expires_at <= now,
            )
            .options(selectinload(PurchaseOrder.offer))
            .order_by(PurchaseOrder.expires_at)
            .limit(EXPIRED_ORDERS_BATCH)
            .with_for_update()
        )
    ).all()

    for order in orders:
        if order.provider != PaymentProvider.YOOKASSA.value or not order.provider_payment_id:
            # Prodamus не имеет API статуса: просроченный заказ просто освобождаем.
            # Поздний подписанный webhook всё равно добавит оплату в пакет.
            await _expire_order(session, order)
            await session.commit()
            continue

        try:
            payment = await _yookassa(
                "GET", f"/payments/{order.provider_payment_id}"
            )
        except PaymentError:
            # Не смогли проверить платёж — не освобождаем слот, чтобы не
            # потерять оплату. Повторим проверку позже, но не задерживаем
            # остальные запросы: выходим после первой же ошибки.
            logger.warning("Не удалось проверить платёж заказа %s", order.id)
            order.expires_at = now + timedelta(
                minutes=get_settings().payment_reservation_minutes
            )
            await session.commit()
            break

        status = payment.get("status")
        if status == "succeeded":
            order_id = order.id
            try:
                _assert_yookassa_payment(order, payment)
                await _apply_paid_order(session, order)
                await session.commit()
            except (PaymentError, IntegrityError):
                # Не блокируем остальные заказы из-за одного проблемного:
                # откладываем его проверку и выходим.
                await session.rollback()
                logger.exception(
                    "Не удалось подтвердить поздний платёж заказа %s", order_id
                )
                await session.execute(
                    update(PurchaseOrder)
                    .where(PurchaseOrder.id == order_id)
                    .values(expires_at=now + timedelta(hours=1))
                )
                await session.commit()
                return
            continue

        if status == "canceled":
            await _expire_order(session, order)
            await session.commit()
            continue

        age = now - _as_utc(order.created_at)
        if age >= timedelta(hours=MAX_PAYMENT_RESERVATION_HOURS):
            try:
                await _yookassa(
                    "POST",
                    f"/payments/{order.provider_payment_id}/cancel",
                    idempotence_key=f"cancel-{order.id}",
                )
            except PaymentError:
                logger.warning("Не удалось отменить зависший платёж %s", order.id)
            await _expire_order(session, order)
        else:
            order.expires_at = now + timedelta(
                minutes=get_settings().payment_reservation_minutes
            )
        await session.commit()


async def create_purchase_payment(
    session: AsyncSession,
    user: User,
    offer_id: UUID,
    slot_id: UUID,
    promo_code: str | None = None,
    provider: PaymentProvider = PaymentProvider.YOOKASSA,
) -> tuple[PurchaseOrder, str]:
    offer = await session.scalar(
        select(IndividualLessonOffer).where(
            IndividualLessonOffer.id == offer_id,
            IndividualLessonOffer.is_active.is_(True),
        )
    )
    if offer is None:
        raise LookupError("Тариф не найден")
    if offer.price_minor is None:
        raise PriceNotSetError("Цена тарифа не установлена")

    await lessons._lock_user(session, user.id)
    slot = await lessons._get_free_slot(session, slot_id)
    await lessons._ensure_no_booking_on_day(session, user, slot)
    if slot.duration_minutes != offer.duration_minutes:
        raise lessons.SlotUnavailableError("Длительность слота не соответствует тарифу")

    now = datetime.now(UTC)
    order_id = uuid4()
    promo = None
    if promo_code:
        promo = await session.scalar(
            select(PromoCode)
            .where(PromoCode.code == promo_code.strip().upper())
            .with_for_update()
        )
        if promo is None or not promo.is_active or promo.used_at is not None:
            raise PromoCodeError("Промокод не найден или уже использован")
        if promo.offer_id != offer.id:
            raise PromoCodeError("Промокод не действует на этот тариф")
        if promo.reserved_order_id is not None:
            reserved = await session.get(PurchaseOrder, promo.reserved_order_id)
            if (
                reserved is not None
                and reserved.status == PurchaseOrderStatus.PENDING.value
            ):
                raise PromoCodeError("Промокод уже используется в другом заказе")
            promo.reserved_order_id = None
        discount_minor, total_minor = discount_amounts(
            offer.price_minor, promo.discount_percent
        )
    else:
        discount_minor, total_minor = 0, offer.price_minor

    settings = get_settings()
    order = PurchaseOrder(
        id=order_id,
        user_id=user.id,
        offer_id=offer.id,
        slot_id=slot.id,
        promo_code_id=promo.id if promo else None,
        price_minor=offer.price_minor,
        discount_minor=discount_minor,
        total_minor=total_minor,
        provider=provider.value,
        status=PurchaseOrderStatus.PENDING.value,
        expires_at=now + timedelta(minutes=settings.payment_reservation_minutes),
    )
    if promo is not None:
        promo.reserved_order_id = order_id

    session.add(order)
    await session.flush()
    slot.status = LessonSlotStatus.BLOCKED.value

    try:
        if provider == PaymentProvider.PRODAMUS:
            if not settings.prodamus_secret_key:
                raise PaymentError("Prodamus не настроен")
            confirmation_url = _prodamus_payment_url(order, offer, user, settings)
        else:
            payment = await _yookassa(
                "POST",
                "/payments",
                body={
                    "amount": {
                        "value": f"{total_minor / 100:.2f}",
                        "currency": order.currency,
                    },
                    "capture": True,
                    "confirmation": {
                        "type": "redirect",
                        "return_url": (
                            f"{settings.yookassa_return_url}/payment/success?order_id={order.id}"
                        ),
                    },
                    "description": f"Индивидуальный урок: {offer.title}",
                    "metadata": {"order_id": str(order.id)},
                },
                idempotence_key=str(order.id),
            )
            confirmation = payment.get("confirmation") or {}
            confirmation_url = confirmation.get("confirmation_url")
            if not payment.get("id") or not confirmation_url:
                raise PaymentError("ЮKassa не вернула ссылку на оплату")
            order.provider_payment_id = payment["id"]
    except PaymentError:
        await session.rollback()
        raise

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise PaymentError("Не удалось создать заказ") from exc

    return order, confirmation_url


async def confirm_payment(session: AsyncSession, payment_id: str) -> bool:
    """Подтверждаем заказ только после актуального статуса из API ЮKassa."""
    order = await session.scalar(
        select(PurchaseOrder)
        .where(PurchaseOrder.provider_payment_id == payment_id)
        .options(selectinload(PurchaseOrder.offer))
        .with_for_update()
    )
    if order is None or order.provider != PaymentProvider.YOOKASSA.value:
        return False
    if order.status == PurchaseOrderStatus.SUCCEEDED.value:
        return True
    if order.status not in {
        PurchaseOrderStatus.PENDING.value,
        PurchaseOrderStatus.EXPIRED.value,
        PurchaseOrderStatus.CANCELLED.value,
    }:
        return False

    current = await _yookassa("GET", f"/payments/{payment_id}")
    if current.get("status") != "succeeded":
        return False

    try:
        _assert_yookassa_payment(order, current)
        await _apply_paid_order(session, order)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise PaymentError("Не удалось подтвердить заказ") from exc
    return True


async def confirm_prodamus_payment(
    session: AsyncSession, values: dict, signature: str | None
) -> bool:
    """Выдаём доступ только по подписанному уведомлению Prodamus."""
    settings = get_settings()
    if not settings.prodamus_secret_key:
        raise PaymentError("Prodamus не настроен")
    if not verify_prodamus_signature(values, signature, settings.prodamus_secret_key):
        raise PaymentError("Подпись уведомления Prodamus не прошла проверку")

    order_num = values.get("order_num")
    if not isinstance(order_num, str):
        return False
    try:
        order_uuid = UUID(order_num)
    except ValueError:
        return False

    order = await session.scalar(
        select(PurchaseOrder)
        .where(PurchaseOrder.id == order_uuid)
        .options(selectinload(PurchaseOrder.offer))
        .with_for_update()
    )
    if order is None or order.provider != PaymentProvider.PRODAMUS.value:
        return False
    if order.status == PurchaseOrderStatus.SUCCEEDED.value:
        return True
    if order.status not in {
        PurchaseOrderStatus.PENDING.value,
        PurchaseOrderStatus.EXPIRED.value,
    }:
        return False
    if str(values.get("payment_status", "")).lower() != "success":
        return False

    _assert_prodamus_payment(order, values)
    internal_id = str(values.get("order_id") or "").strip()
    if not internal_id:
        raise PaymentError("Prodamus не вернул номер платежа")
    if order.provider_payment_id and order.provider_payment_id != internal_id:
        raise PaymentError("Номер платежа Prodamus не совпадает с заказом")
    order.provider_payment_id = internal_id

    try:
        await _apply_paid_order(session, order)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise PaymentError("Не удалось подтвердить заказ Prodamus") from exc
    except PaymentError:
        await session.rollback()
        raise
    return True


async def cancel_payment(session: AsyncSession, payment_id: str) -> bool:
    """Отмену тоже проверяем через API: поддельный webhook не освободит слот."""
    order = await session.scalar(
        select(PurchaseOrder)
        .where(PurchaseOrder.provider_payment_id == payment_id)
        .with_for_update()
    )
    if order is None or order.provider != PaymentProvider.YOOKASSA.value:
        return False
    if order.status in {
        PurchaseOrderStatus.SUCCEEDED.value,
        PurchaseOrderStatus.CANCELLED.value,
    }:
        return True
    if order.status not in {
        PurchaseOrderStatus.PENDING.value,
        PurchaseOrderStatus.EXPIRED.value,
    }:
        return False

    current = await _yookassa("GET", f"/payments/{payment_id}")
    if current.get("status") != "canceled":
        return False

    order.status = PurchaseOrderStatus.CANCELLED.value
    await _release_promo_reservation(session, order)
    await _release_slot(session, order)
    await session.commit()
    return True


async def get_user_order(
    session: AsyncSession, order_id: UUID, user: User
) -> PurchaseOrder | None:
    return await session.scalar(
        select(PurchaseOrder).where(
            PurchaseOrder.id == order_id,
            PurchaseOrder.user_id == user.id,
        )
    )
