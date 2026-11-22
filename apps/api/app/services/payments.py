from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.individual_lessons import (
    IndividualLessonOffer,
    LessonPackage,
    LessonPackageStatus,
    LessonSlot,
    LessonSlotStatus,
)
from app.models.payments import PromoCode, PurchaseOrder, PurchaseOrderStatus
from app.models.user import User
from app.services import individual_lessons as lessons


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


async def release_expired_orders(session: AsyncSession) -> None:
    now = datetime.now(UTC)
    orders = (
        await session.scalars(
            select(PurchaseOrder).where(
                PurchaseOrder.status == PurchaseOrderStatus.PENDING.value,
                PurchaseOrder.expires_at <= now,
            )
        )
    ).all()
    for order in orders:
        order.status = PurchaseOrderStatus.EXPIRED.value
        slot = await session.scalar(
            select(LessonSlot).where(
                LessonSlot.id == order.slot_id,
                LessonSlot.status == LessonSlotStatus.BLOCKED.value,
            )
        )
        if slot is not None:
            slot.status = LessonSlotStatus.FREE.value
    if orders:
        await session.commit()


async def create_purchase_payment(
    session: AsyncSession,
    user: User,
    offer_id: UUID,
    slot_id: UUID,
    promo_code: str | None = None,
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

    promo = None
    if promo_code:
        promo = await session.scalar(
            select(PromoCode)
            .where(PromoCode.code == promo_code.strip().upper())
            .with_for_update()
        )
        if promo is None or not promo.is_active or promo.used_at is not None:
            raise PromoCodeError("Промокод не найден или уже использован")
        discount_minor, total_minor = discount_amounts(offer.price_minor, promo.discount_percent)
    else:
        discount_minor, total_minor = 0, offer.price_minor

    settings = get_settings()
    now = datetime.now(UTC)
    order = PurchaseOrder(
        user_id=user.id,
        offer_id=offer.id,
        slot_id=slot.id,
        promo_code_id=promo.id if promo else None,
        price_minor=offer.price_minor,
        discount_minor=discount_minor,
        total_minor=total_minor,
        status=PurchaseOrderStatus.PENDING.value,
        expires_at=now + timedelta(minutes=settings.payment_reservation_minutes),
    )
    session.add(order)
    await session.flush()
    slot.status = LessonSlotStatus.BLOCKED.value

    try:
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
    except PaymentError:
        await session.rollback()
        raise

    confirmation = payment.get("confirmation") or {}
    confirmation_url = confirmation.get("confirmation_url")
    if not payment.get("id") or not confirmation_url:
        await session.rollback()
        raise PaymentError("ЮKassa не вернула ссылку на оплату")

    order.yookassa_payment_id = payment["id"]
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise PaymentError("Не удалось создать заказ") from exc

    return order, confirmation_url


async def confirm_payment(session: AsyncSession, payment_id: str) -> bool:
    order = await session.scalar(
        select(PurchaseOrder)
        .where(PurchaseOrder.yookassa_payment_id == payment_id)
        .options(selectinload(PurchaseOrder.offer))
    )
    if order is None:
        return False
    if order.status == PurchaseOrderStatus.SUCCEEDED.value:
        return True
    if order.status != PurchaseOrderStatus.PENDING.value:
        return False

    payment = await _yookassa("GET", f"/payments/{payment_id}")
    if payment.get("status") != "succeeded":
        return False
    if Decimal(payment["amount"]["value"]) != Decimal(order.total_minor) / Decimal(100):
        raise PaymentError("Сумма платежа не совпадает с заказом")
    if (payment.get("metadata") or {}).get("order_id") != str(order.id):
        raise PaymentError("Платёж не соответствует заказу")

    slot = await session.scalar(
        select(LessonSlot)
        .where(
            LessonSlot.id == order.slot_id,
            LessonSlot.status == LessonSlotStatus.BLOCKED.value,
        )
        .with_for_update()
    )
    if slot is None:
        raise PaymentError("Слот заказа уже недоступен")

    if order.promo_code_id is not None:
        promo = await session.scalar(
            select(PromoCode).where(PromoCode.id == order.promo_code_id).with_for_update()
        )
        if promo is not None and promo.used_at is None:
            promo.used_at = datetime.now(UTC)

    user = await session.get(User, order.user_id)
    if user is None:
        raise PaymentError("Пользователь заказа не найден")

    slot.status = LessonSlotStatus.BOOKED.value
    now = datetime.now(UTC)
    offer = order.offer
    package = LessonPackage(
        user_id=user.id,
        offer_id=offer.id,
        total_lessons=offer.lessons_count,
        remaining_lessons=offer.lessons_count,
        status=LessonPackageStatus.ACTIVE.value,
        expires_at=now + timedelta(days=offer.validity_days) if offer.validity_days else None,
    )
    session.add(package)
    await session.flush()
    await session.refresh(package, attribute_names=["offer"])
    await lessons._create_booking(session, user, package, slot)
    order.status = PurchaseOrderStatus.SUCCEEDED.value
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise PaymentError("Не удалось подтвердить заказ") from exc
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
