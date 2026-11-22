from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db import get_session
from app.models.user import User, UserRole
from app.schemas.admin import OfferPriceIn, PromoCodeIn, PromoCodeOut
from app.schemas.auth import UserOut
from app.schemas.individual_lessons import IndividualLessonOfferOut
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


@router.get("/products", response_model=list[IndividualLessonOfferOut])
async def list_products(
    _: User = Depends(require_roles(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> list[IndividualLessonOfferOut]:
    offers = await admin_service.list_offers(session)
    return [IndividualLessonOfferOut(**lessons_service.offer_out_data(offer)) for offer in offers]


@router.patch("/products/{slug}/price", response_model=IndividualLessonOfferOut)
async def update_product_price(
    slug: str,
    payload: OfferPriceIn,
    _: User = Depends(require_roles(UserRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
) -> IndividualLessonOfferOut:
    try:
        offer = await admin_service.set_offer_price(session, slug, payload.price)
    except admin_service.OfferNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=UNPROCESSABLE, detail=str(exc)) from exc
    return IndividualLessonOfferOut(**lessons_service.offer_out_data(offer))


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
            session, payload.percent, payload.code
        )
    except admin_service.PromoCodeExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=UNPROCESSABLE, detail=str(exc)) from exc
    return PromoCodeOut.model_validate(promo)
