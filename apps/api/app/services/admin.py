from __future__ import annotations

import secrets
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.individual_lessons import IndividualLessonOffer
from app.models.payments import PromoCode


class OfferNotFoundError(Exception):
    pass


class PromoCodeExistsError(Exception):
    pass


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


async def list_offers(session: AsyncSession) -> list[IndividualLessonOffer]:
    result = await session.scalars(
        select(IndividualLessonOffer).order_by(
            IndividualLessonOffer.position, IndividualLessonOffer.slug
        )
    )
    return list(result)


async def set_offer_price(
    session: AsyncSession, slug: str, price: Decimal
) -> IndividualLessonOffer:
    price_minor = price_to_minor(price)
    offer = await session.scalar(
        select(IndividualLessonOffer).where(IndividualLessonOffer.slug == slug)
    )
    if offer is None:
        raise OfferNotFoundError(f"Тариф не найден: {slug}")

    offer.price_minor = price_minor
    await session.commit()
    return offer


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
