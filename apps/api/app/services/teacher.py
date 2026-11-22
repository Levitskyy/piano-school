from __future__ import annotations

from uuid import UUID

from pydantic import HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.individual_lessons import LessonBooking, LessonPackage, LessonSlot
from app.schemas.teacher import TeacherLessonBookingOut
from app.services import individual_lessons as individual_lessons_service


def booking_out(booking: LessonBooking) -> TeacherLessonBookingOut:
    return TeacherLessonBookingOut(
        id=booking.id,
        student_id=booking.user_id,
        student_name=booking.user.name,
        student_email=booking.user.email,
        offer_title=booking.package.offer.title,
        status=booking.status,
        starts_at=booking.slot.starts_at,
        ends_at=booking.slot.ends_at,
        meeting_url=booking.meeting_url,
        created_at=booking.created_at,
    )


def booking_query():
    return (
        select(LessonBooking)
        .join(LessonSlot, LessonBooking.slot_id == LessonSlot.id)
        .options(
            selectinload(LessonBooking.user),
            selectinload(LessonBooking.package).selectinload(LessonPackage.offer),
            selectinload(LessonBooking.slot),
        )
        .order_by(LessonSlot.starts_at)
    )


async def list_bookings(session: AsyncSession) -> list[TeacherLessonBookingOut]:
    result = await session.scalars(booking_query())
    return [booking_out(booking) for booking in result.all()]


async def update_meeting_url(
    session: AsyncSession,
    booking_id: UUID,
    meeting_url: HttpUrl | None,
) -> TeacherLessonBookingOut:
    booking = await session.scalar(
        booking_query().where(LessonBooking.id == booking_id)
    )
    if booking is None:
        raise LookupError("Запись не найдена")

    booking.meeting_url = str(meeting_url) if meeting_url else None
    await session.commit()
    return booking_out(booking)


async def _reload_booking(
    session: AsyncSession, booking_id: UUID
) -> TeacherLessonBookingOut:
    booking = await session.scalar(
        booking_query().where(LessonBooking.id == booking_id)
    )
    if booking is None:
        raise LookupError("Запись не найдена")
    return booking_out(booking)


async def cancel_booking(
    session: AsyncSession, booking_id: UUID
) -> TeacherLessonBookingOut:
    try:
        await individual_lessons_service.cancel_booking(
            session, booking_id, allow_late=True
        )
    except individual_lessons_service.BookingNotFoundError as exc:
        raise LookupError(str(exc)) from exc
    return await _reload_booking(session, booking_id)

