from __future__ import annotations

import re
import secrets
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.individual_lessons import (
    IndividualLessonOffer,
    IndividualLessonOfferKind,
    LessonPackage,
)
from app.models.payments import PromoCode, PurchaseOrder


class OfferNotFoundError(Exception):
    pass


class OfferSlugExistsError(Exception):
    pass


class OfferInUseError(Exception):
    pass


class PromoCodeExistsError(Exception):
    pass


OFFER_IN_USE_MESSAGE = (
    "Тариф используется в заказах, пакетах или промокодах. "
    "Скройте его вместо удаления, чтобы сохранить историю."
)

TRANSLIT = str.maketrans(
    "абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
    "abvgdeejzijklmnoprstufhzcss_y_eua",
)


def price_to_minor(value: Decimal) -> int:
    price = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if price <= 0:
        raise ValueError("Цена должна быть больше нуля")
    return int(price * 100)


def normalize_percent(value: Decimal) -> Decimal:
    percent = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if not Decimal("0") < percent <= Decimal("100"):
        raise ValueError("Процент должен быть больше 0 и не больше 100")
    return percent


def normalize_code(code: str | None) -> str:
    cleaned = (code or "").strip().upper()
    if not cleaned:
        cleaned = secrets.token_hex(4).upper()
    if len(cleaned) > 32:
        raise ValueError("Код не должен длиннее 32 символов")
    if any(character.isspace() for character in cleaned):
        raise ValueError("Код не должен содержать пробелы")
    return cleaned


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower().translate(TRANSLIT))
    return slug[:80].strip("-") or "offer"


async def unique_slug(session: AsyncSession, value: str) -> str:
    base = slugify(value)
    candidate = base
    suffix = 2
    while await session.scalar(
        select(IndividualLessonOffer.id).where(IndividualLessonOffer.slug == candidate)
    ):
        tail = f"-{suffix}"
        candidate = f"{base[: 80 - len(tail)].rstrip('-')}{tail}"
        suffix += 1
    return candidate


async def list_offers(session: AsyncSession) -> list[IndividualLessonOffer]:
    result = await session.scalars(
        select(IndividualLessonOffer).order_by(
            IndividualLessonOffer.position, IndividualLessonOffer.slug
        )
    )
    return list(result)


async def get_offer(session: AsyncSession, slug: str) -> IndividualLessonOffer:
    offer = await session.scalar(
        select(IndividualLessonOffer).where(IndividualLessonOffer.slug == slug)
    )
    if offer is None:
        raise OfferNotFoundError(f"Тариф не найден: {slug}")
    return offer


async def set_offer_price(
    session: AsyncSession, slug: str, price: Decimal
) -> IndividualLessonOffer:
    price_minor = price_to_minor(price)
    offer = await get_offer(session, slug)
    offer.price_minor = price_minor
    await session.commit()
    return offer


async def create_offer(
    session: AsyncSession,
    *,
    title: str,
    description: str,
    lessons_count: int,
    price: Decimal,
    is_active: bool,
    slug: str | None = None,
    validity_days: int | None = None,
) -> IndividualLessonOffer:
    cleaned_title = title.strip()
    if not cleaned_title:
        raise ValueError("Название не может быть пустым")

    if slug is not None:
        chosen_slug = slugify(slug)
        if await session.scalar(
            select(IndividualLessonOffer.id).where(
                IndividualLessonOffer.slug == chosen_slug
            )
        ):
            raise OfferSlugExistsError(f"Такой ключ тарифа уже есть: {chosen_slug}")
    else:
        chosen_slug = await unique_slug(session, cleaned_title)

    last_position = await session.scalar(select(func.max(IndividualLessonOffer.position)))

    offer = IndividualLessonOffer(
        slug=chosen_slug,
        title=cleaned_title,
        description=description.strip(),
        kind=(
            IndividualLessonOfferKind.SINGLE.value
            if lessons_count == 1
            else IndividualLessonOfferKind.PACKAGE.value
        ),
        lessons_count=lessons_count,
        duration_minutes=60,
        price_minor=price_to_minor(price),
        currency="RUB",
        validity_days=validity_days,
        is_active=is_active,
        position=(last_position or 0) + 1,
    )
    session.add(offer)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise OfferSlugExistsError(f"Такой ключ тарифа уже есть: {offer.slug}") from exc
    return offer


async def update_offer(
    session: AsyncSession,
    slug: str,
    *,
    title: str | None = None,
    description: str | None = None,
    lessons_count: int | None = None,
    price: Decimal | None = None,
    validity_days: int | None = None,
    set_validity_days: bool = False,
    is_active: bool | None = None,
) -> IndividualLessonOffer:
    offer = await get_offer(session, slug)

    if title is not None:
        cleaned_title = title.strip()
        if not cleaned_title:
            raise ValueError("Название не может быть пустым")
        offer.title = cleaned_title
    if description is not None:
        offer.description = description.strip()
    if lessons_count is not None:
        offer.lessons_count = lessons_count
        offer.kind = (
            IndividualLessonOfferKind.SINGLE.value
            if lessons_count == 1
            else IndividualLessonOfferKind.PACKAGE.value
        )
    if price is not None:
        offer.price_minor = price_to_minor(price)
    if set_validity_days:
        offer.validity_days = validity_days
    if is_active is not None:
        offer.is_active = is_active

    await session.commit()
    return offer


async def delete_offer(session: AsyncSession, slug: str) -> None:
    offer = await get_offer(session, slug)

    for model in (LessonPackage, PurchaseOrder, PromoCode):
        linked = await session.scalar(
            select(model.id).where(model.offer_id == offer.id).limit(1)
        )
        if linked is not None:
            raise OfferInUseError(OFFER_IN_USE_MESSAGE)

    await session.delete(offer)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise OfferInUseError(OFFER_IN_USE_MESSAGE) from exc


async def list_promo_codes(session: AsyncSession) -> list[PromoCode]:
    result = await session.scalars(
        select(PromoCode).order_by(PromoCode.created_at.desc()).limit(100)
    )
    return list(result)


async def create_promo_code(
    session: AsyncSession, percent: Decimal, offer_slug: str, code: str | None = None
) -> PromoCode:
    offer = await session.scalar(
        select(IndividualLessonOffer).where(IndividualLessonOffer.slug == offer_slug.strip())
    )
    if offer is None:
        raise OfferNotFoundError(f"Тариф не найден: {offer_slug}")

    promo = PromoCode(
        code=normalize_code(code),
        discount_percent=normalize_percent(percent),
        offer_id=offer.id,
    )
    session.add(promo)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise PromoCodeExistsError(f"Промокод уже существует: {promo.code}") from exc
    return promo
