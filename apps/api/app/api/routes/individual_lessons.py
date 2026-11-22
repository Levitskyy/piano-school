from uuid import UUID

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
    RescheduleLessonIn,
)
from app.schemas.payments import PurchasePaymentIn, PurchasePaymentOut
from app.services import individual_lessons as individual_lessons_service
from app.services import payments as payments_service

router = APIRouter(prefix="/individual-lessons", tags=["individual-lessons"])


@router.get("/offers", response_model=list[IndividualLessonOfferOut])
async def list_offers(
    session: AsyncSession = Depends(get_session),
) -> list[IndividualLessonOfferOut]:
    offers = await individual_lessons_service.list_offers(session)
    return [IndividualLessonOfferOut(**offer) for offer in offers]


@router.get("/slots", response_model=list[LessonSlotOut])
async def list_slots(
    exclude_booking: UUID | None = None,
    user: User | None = Depends(get_optional_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[LessonSlotOut]:
    await payments_service.release_expired_orders(session)
    slots = await individual_lessons_service.list_free_slots(
        session, user, exclude_booking_id=exclude_booking
    )
    return [LessonSlotOut(**slot) for slot in slots]


@router.get("/account", response_model=AccountIndividualLessonsOut)
async def get_account_lessons(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AccountIndividualLessonsOut:
    return await individual_lessons_service.get_account_lessons(session, user)


@router.post("/purchase", response_model=PurchasePaymentOut)
async def purchase_lesson(
    payload: PurchasePaymentIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PurchasePaymentOut:
    await payments_service.release_expired_orders(session)
    try:
        order, confirmation_url = await payments_service.create_purchase_payment(
            session, user, payload.offer_id, payload.slot_id, payload.promo_code
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (
        individual_lessons_service.SlotUnavailableError,
        payments_service.PromoCodeError,
        payments_service.PriceNotSetError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except payments_service.PaymentError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return PurchasePaymentOut(
        order_id=order.id,
        status=order.status,
        total_minor=order.total_minor,
        discount_minor=order.discount_minor,
        currency=order.currency,
        confirmation_url=confirmation_url,
    )


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


@router.post("/bookings/{booking_id}/cancel", response_model=LessonBookingOut)
async def cancel_lesson(
    booking_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> LessonBookingOut:
    try:
        return await individual_lessons_service.cancel_booking(
            session, booking_id, user=user
        )
    except individual_lessons_service.BookingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except individual_lessons_service.BookingUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/bookings/{booking_id}/reschedule", response_model=LessonBookingOut)
async def reschedule_lesson(
    booking_id: UUID,
    payload: RescheduleLessonIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> LessonBookingOut:
    try:
        return await individual_lessons_service.reschedule_booking(
            session, booking_id, payload.slot_id, user=user
        )
    except individual_lessons_service.BookingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (
        individual_lessons_service.BookingUnavailableError,
        individual_lessons_service.SlotUnavailableError,
    ) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
