from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db import get_session
from app.models.individual_lessons import IndividualLessonOffer
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminOfferOut,
    OfferCreateIn,
    OfferPriceIn,
    OfferUpdateIn,
    PromoCodeIn,
    PromoCodeOut,
)
from app.schemas.auth import UserOut
from app.services import admin as admin_service
from app.services import individual_lessons as lessons_service

router = APIRouter(prefix="/admin", tags=["admin"])

UNPROCESSABLE = status.HTTP_422_UNPROCESSABLE_CONTENT


@router.get("/users", response_model=list[UserOut])
async def list_users(
    _: User = Depends(require_roles(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> list[User]:
    result = await session.scalars(
        select(User).order_by(User.created_at.desc()).limit(100)
    )
    return list(result)


def admin_offer_out(offer: IndividualLessonOffer) -> AdminOfferOut:
    data = lessons_service.offer_out_data(offer)
    data["is_active"] = offer.is_active
    data["position"] = offer.position
    return AdminOfferOut(**data)


@router.get("/products", response_model=list[AdminOfferOut])
async def list_products(
    _: User = Depends(require_roles(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> list[AdminOfferOut]:
    offers = await admin_service.list_offers(session)
    return [admin_offer_out(offer) for offer in offers]


@router.post(
    "/products",
    response_model=AdminOfferOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    payload: OfferCreateIn,
    _: User = Depends(require_roles(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> AdminOfferOut:
    try:
        offer = await admin_service.create_offer(
            session,
            title=payload.title,
            slug=payload.slug,
            description=payload.description,
            lessons_count=payload.lessons_count,
            price=payload.price,
            validity_days=payload.validity_days,
            is_active=payload.is_active,
        )
    except admin_service.OfferSlugExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=UNPROCESSABLE, detail=str(exc)) from exc
    return admin_offer_out(offer)


@router.patch("/products/{slug}", response_model=AdminOfferOut)
async def update_product(
    slug: str,
    payload: OfferUpdateIn,
    _: User = Depends(require_roles(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> AdminOfferOut:
    validity_days_provided = "validity_days" in payload.model_fields_set
    try:
        offer = await admin_service.update_offer(
            session,
            slug,
            title=payload.title,
            description=payload.description,
            lessons_count=payload.lessons_count,
            price=payload.price,
            validity_days=payload.validity_days,
            set_validity_days=validity_days_provided,
            is_active=payload.is_active,
        )
    except admin_service.OfferNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=UNPROCESSABLE, detail=str(exc)) from exc
    return admin_offer_out(offer)


@router.patch("/products/{slug}/price", response_model=AdminOfferOut)
async def update_product_price(
    slug: str,
    payload: OfferPriceIn,
    _: User = Depends(require_roles(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> AdminOfferOut:
    try:
        offer = await admin_service.set_offer_price(session, slug, payload.price)
    except admin_service.OfferNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=UNPROCESSABLE, detail=str(exc)) from exc
    return admin_offer_out(offer)


@router.delete("/products/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    slug: str,
    _: User = Depends(require_roles(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> None:
    try:
        await admin_service.delete_offer(session, slug)
    except admin_service.OfferNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except admin_service.OfferInUseError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/promo-codes", response_model=list[PromoCodeOut])
async def list_promo_codes(
    _: User = Depends(require_roles(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> list[PromoCodeOut]:
    promo_codes = await admin_service.list_promo_codes(session)
    return [PromoCodeOut.model_validate(promo) for promo in promo_codes]


@router.post(
    "/promo-codes",
    response_model=PromoCodeOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_promo_code(
    payload: PromoCodeIn,
    _: User = Depends(require_roles(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> PromoCodeOut:
    try:
        promo = await admin_service.create_promo_code(
            session, payload.percent, payload.offer_slug, payload.code
        )
    except admin_service.OfferNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except admin_service.PromoCodeExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=UNPROCESSABLE, detail=str(exc)) from exc
    return PromoCodeOut.model_validate(promo)
