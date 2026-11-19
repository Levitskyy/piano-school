from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_optional_current_user
from app.db import get_session
from app.models.user import User
from app.schemas.individual_lessons import (
    AccountIndividualLessonsOut,
    BookFromPackageIn,
    IndividualLessonOfferOut,
    LessonBookingOut,
    LessonSlotOut,
    PurchaseIndividualLessonIn,
    PurchaseResultOut,
)
from app.services import individual_lessons as individual_lessons_service

router = APIRouter(prefix="/individual-lessons", tags=["individual-lessons"])


@router.get("/offers", response_model=list[IndividualLessonOfferOut])
async def list_offers(
    session: AsyncSession = Depends(get_session),
) -> list[IndividualLessonOfferOut]:
    offers = await individual_lessons_service.list_offers(session)
    return [IndividualLessonOfferOut(**offer) for offer in offers]


@router.get("/slots", response_model=list[LessonSlotOut])
async def list_slots(
    user: User | None = Depends(get_optional_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[LessonSlotOut]:
    slots = await individual_lessons_service.list_free_slots(session, user)
    return [LessonSlotOut(**slot) for slot in slots]


@router.get("/account", response_model=AccountIndividualLessonsOut)
async def get_account_lessons(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AccountIndividualLessonsOut:
    return await individual_lessons_service.get_account_lessons(session, user)


@router.post("/purchase", response_model=PurchaseResultOut)
async def purchase_lesson(
    payload: PurchaseIndividualLessonIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PurchaseResultOut:
    try:
        booking, package = await individual_lessons_service.purchase_and_book(
            session, user, payload.offer_id, payload.slot_id
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except individual_lessons_service.SlotUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return PurchaseResultOut(booking=booking, package=package)


@router.post("/book", response_model=LessonBookingOut)
async def book_from_package(
    payload: BookFromPackageIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> LessonBookingOut:
    try:
        return await individual_lessons_service.book_from_package(
            session, user, payload.package_id, payload.slot_id
        )
    except individual_lessons_service.PackageUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except individual_lessons_service.SlotUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
