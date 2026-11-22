from __future__ import annotations

from datetime import UTC, datetime, timedelta, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.individual_lessons import (
    IndividualLessonOffer,
    LessonBooking,
    LessonBookingStatus,
    LessonPackage,
    LessonPackageStatus,
    LessonSlot,
    LessonSlotStatus,
)
from app.models.user import User
from app.schemas.individual_lessons import (
    AccountIndividualLessonsOut,
    LessonBookingOut,
    LessonPackageOut,
)

SLOT_LOOKAHEAD_DAYS = 60


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def user_timezone(user: User) -> tzinfo:
    try:
        return ZoneInfo(user.timezone)
    except (ZoneInfoNotFoundError, ValueError):
        return UTC


def local_day_key(value: datetime, tz: tzinfo) -> str:
    return as_utc(value).astimezone(tz).date().isoformat()


class SlotUnavailableError(Exception):
    pass


class PackageUnavailableError(Exception):
    pass


class BookingNotFoundError(Exception):
    pass


class BookingUnavailableError(Exception):
    pass


def offer_out_data(offer: IndividualLessonOffer) -> dict:
    return {
        "id": offer.id,
        "slug": offer.slug,
        "title": offer.title,
        "description": offer.description,
        "kind": offer.kind,
        "lessons_count": offer.lessons_count,
        "duration_minutes": offer.duration_minutes,
        "price_minor": offer.price_minor,
        "currency": offer.currency,
        "validity_days": offer.validity_days,
    }


def slot_out_data(slot: LessonSlot) -> dict:
    return {
        "id": slot.id,
        "starts_at": slot.starts_at,
        "ends_at": slot.ends_at,
        "duration_minutes": slot.duration_minutes,
    }


def package_out_data(package: LessonPackage) -> LessonPackageOut:
    return LessonPackageOut(
        id=package.id,
        offer_slug=package.offer.slug,
        offer_title=package.offer.title,
        total_lessons=package.total_lessons,
        remaining_lessons=package.remaining_lessons,
        status=package.status,
        expires_at=package.expires_at,
        created_at=package.created_at,
    )


def booking_out_data(booking: LessonBooking) -> LessonBookingOut:
    now = datetime.now(UTC)
    starts_at = as_utc(booking.slot.starts_at)
    can_change = (
        booking.status == LessonBookingStatus.CONFIRMED.value
        and starts_at > now
        and starts_at - now
        >= timedelta(hours=get_settings().lesson_cancellation_hours)
    )
    return LessonBookingOut(
        id=booking.id,
        package_id=booking.package_id,
        offer_title=booking.package.offer.title,
        status=booking.status,
        starts_at=booking.slot.starts_at,
        ends_at=booking.slot.ends_at,
        meeting_url=booking.meeting_url,
        can_change=can_change,
        created_at=booking.created_at,
    )


async def booked_day_keys(
    session: AsyncSession,
    user: User,
    exclude_booking_id=None,
) -> set[str]:
    query = (
        select(LessonSlot.starts_at)
        .join(LessonBooking, LessonBooking.slot_id == LessonSlot.id)
        .where(
            LessonBooking.user_id == user.id,
            LessonBooking.status.in_(
                [LessonBookingStatus.CONFIRMED.value, LessonBookingStatus.COMPLETED.value]
            ),
        )
    )
    if exclude_booking_id is not None:
        query = query.where(LessonBooking.id != exclude_booking_id)
    result = await session.scalars(query)
    tz = user_timezone(user)
    return {local_day_key(starts_at, tz) for starts_at in result.all()}


async def list_offers(session: AsyncSession) -> list[dict]:
    result = await session.scalars(
        select(IndividualLessonOffer)
        .where(IndividualLessonOffer.is_active.is_(True))
        .order_by(IndividualLessonOffer.position, IndividualLessonOffer.created_at)
    )
    return [offer_out_data(offer) for offer in result.all()]


async def list_free_slots(
    session: AsyncSession,
    user: User | None = None,
    exclude_booking_id=None,
) -> list[dict]:
    now = datetime.now(UTC)
    until = now + timedelta(days=SLOT_LOOKAHEAD_DAYS)
    result = await session.scalars(
        select(LessonSlot)
        .where(
            LessonSlot.status == LessonSlotStatus.FREE.value,
            LessonSlot.starts_at > now,
            LessonSlot.starts_at <= until,
        )
        .order_by(LessonSlot.starts_at)
    )
    slots = result.all()
    if user is not None:
        booked_days = await booked_day_keys(
            session, user, exclude_booking_id=exclude_booking_id
        )
        tz = user_timezone(user)
        slots = [
            slot
            for slot in slots
            if local_day_key(slot.starts_at, tz) not in booked_days
        ]
    return [slot_out_data(slot) for slot in slots]


async def _lock_user(session: AsyncSession, user_id) -> None:
    await session.scalar(select(User).where(User.id == user_id).with_for_update())


async def _ensure_no_booking_on_day(
    session: AsyncSession,
    user: User,
    slot: LessonSlot,
    exclude_booking_id=None,
) -> None:
    booked_days = await booked_day_keys(
        session, user, exclude_booking_id=exclude_booking_id
    )
    if local_day_key(slot.starts_at, user_timezone(user)) in booked_days:
        raise SlotUnavailableError(
            "На этот день у вас уже есть занятие. Выберите следующий день."
        )


async def _get_free_slot(session: AsyncSession, slot_id) -> LessonSlot:
    slot = await session.scalar(
        select(LessonSlot)
        .where(
            LessonSlot.id == slot_id,
            LessonSlot.status == LessonSlotStatus.FREE.value,
            LessonSlot.starts_at > datetime.now(UTC),
        )
        .with_for_update()
    )
    if slot is None:
        raise SlotUnavailableError("Слот уже занят или недоступен")
    return slot


async def _create_booking(
    session: AsyncSession,
    user: User,
    package: LessonPackage,
    slot: LessonSlot,
) -> LessonBooking:
    package.remaining_lessons -= 1
    if package.remaining_lessons == 0:
        package.status = LessonPackageStatus.EXHAUSTED.value
    slot.status = LessonSlotStatus.BOOKED.value

    booking = LessonBooking(
        user_id=user.id,
        package_id=package.id,
        slot_id=slot.id,
        status=LessonBookingStatus.CONFIRMED.value,
    )
    session.add(booking)
    await session.flush()
    await session.refresh(booking, attribute_names=["package", "slot"])
    return booking


async def purchase_and_book(
    session: AsyncSession,
    user: User,
    offer_id,
    slot_id,
) -> tuple[LessonBookingOut, LessonPackageOut]:
    offer = await session.scalar(
        select(IndividualLessonOffer).where(
            IndividualLessonOffer.id == offer_id,
            IndividualLessonOffer.is_active.is_(True),
        )
    )
    if offer is None:
        raise LookupError("Тариф не найден")

    await _lock_user(session, user.id)
    slot = await _get_free_slot(session, slot_id)
    await _ensure_no_booking_on_day(session, user, slot)
    if slot.duration_minutes != offer.duration_minutes:
        raise SlotUnavailableError("Длительность слота не соответствует тарифу")

    now = datetime.now(UTC)
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

    booking = await _create_booking(session, user, package, slot)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise SlotUnavailableError("Слот уже занят") from exc

    return booking_out_data(booking), package_out_data(package)


async def book_from_package(
    session: AsyncSession,
    user: User,
    package_id,
    slot_id,
) -> LessonBookingOut:
    package = await session.scalar(
        select(LessonPackage)
        .where(
            LessonPackage.id == package_id,
            LessonPackage.user_id == user.id,
            LessonPackage.status == LessonPackageStatus.ACTIVE.value,
            LessonPackage.remaining_lessons > 0,
        )
        .options(selectinload(LessonPackage.offer))
        .with_for_update()
    )
    if package is None:
        raise PackageUnavailableError("У вас нет доступного пакета занятий")
    if package.expires_at and as_utc(package.expires_at) <= datetime.now(UTC):
        package.status = LessonPackageStatus.EXPIRED.value
        await session.commit()
        raise PackageUnavailableError("Срок действия пакета истёк")

    await _lock_user(session, user.id)
    slot = await _get_free_slot(session, slot_id)
    await _ensure_no_booking_on_day(session, user, slot)
    if slot.duration_minutes != package.offer.duration_minutes:
        raise SlotUnavailableError("Длительность слота не соответствует тарифу")

    booking = await _create_booking(session, user, package, slot)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise SlotUnavailableError("Слот уже занят") from exc

    return booking_out_data(booking)


def _booking_query():
    return select(LessonBooking).options(
        selectinload(LessonBooking.package).selectinload(LessonPackage.offer),
        selectinload(LessonBooking.slot),
        selectinload(LessonBooking.user),
    )


async def _get_booking(
    session: AsyncSession,
    booking_id,
    *,
    user_id=None,
    for_update: bool = False,
) -> LessonBooking | None:
    query = _booking_query().where(LessonBooking.id == booking_id)
    if user_id is not None:
        query = query.where(LessonBooking.user_id == user_id)
    if for_update:
        query = query.with_for_update()
    return await session.scalar(query)


def _ensure_booking_can_change(booking: LessonBooking, *, allow_late: bool) -> None:
    now = datetime.now(UTC)
    starts_at = as_utc(booking.slot.starts_at)
    if starts_at <= now:
        raise BookingUnavailableError("Занятие уже началось")
    if allow_late:
        return
    hours = get_settings().lesson_cancellation_hours
    if starts_at - now < timedelta(hours=hours):
        raise BookingUnavailableError(
            f"Изменить занятие можно не позднее чем за {hours} ч. Напишите преподавателю."
        )


def _return_lesson_to_package(package: LessonPackage) -> None:
    if package.status == LessonPackageStatus.CANCELLED.value:
        return
    package.remaining_lessons = min(
        package.total_lessons, package.remaining_lessons + 1
    )
    if package.status == LessonPackageStatus.EXHAUSTED.value:
        expires_at = as_utc(package.expires_at) if package.expires_at else None
        if expires_at is None or expires_at > datetime.now(UTC):
            package.status = LessonPackageStatus.ACTIVE.value


async def cancel_booking(
    session: AsyncSession,
    booking_id,
    *,
    user: User | None = None,
    allow_late: bool = False,
) -> LessonBookingOut:
    booking = await _get_booking(
        session,
        booking_id,
        user_id=user.id if user is not None else None,
        for_update=True,
    )
    if booking is None:
        raise BookingNotFoundError("Запись не найдена")
    if booking.status != LessonBookingStatus.CONFIRMED.value:
        raise BookingUnavailableError("Занятие уже отменено или завершено")
    _ensure_booking_can_change(booking, allow_late=allow_late)

    booking.status = LessonBookingStatus.CANCELLED.value
    if booking.slot.status == LessonSlotStatus.BOOKED.value:
        booking.slot.status = LessonSlotStatus.FREE.value
    _return_lesson_to_package(booking.package)
    await session.commit()

    updated = await _get_booking(session, booking.id)
    if updated is None:
        raise BookingNotFoundError("Запись не найдена")
    return booking_out_data(updated)


async def reschedule_booking(
    session: AsyncSession,
    booking_id,
    new_slot_id,
    *,
    user: User | None = None,
    allow_late: bool = False,
) -> LessonBookingOut:
    booking = await _get_booking(
        session,
        booking_id,
        user_id=user.id if user is not None else None,
        for_update=True,
    )
    if booking is None:
        raise BookingNotFoundError("Запись не найдена")
    if booking.status != LessonBookingStatus.CONFIRMED.value:
        raise BookingUnavailableError("Занятие уже отменено или завершено")
    _ensure_booking_can_change(booking, allow_late=allow_late)
    if booking.slot_id == new_slot_id:
        return booking_out_data(booking)

    new_slot = await _get_free_slot(session, new_slot_id)
    if new_slot.duration_minutes != booking.package.offer.duration_minutes:
        raise SlotUnavailableError("Длительность слота не соответствует тарифу")
    await _ensure_no_booking_on_day(
        session, booking.user, new_slot, exclude_booking_id=booking.id
    )

    booking.slot.status = LessonSlotStatus.FREE.value
    new_slot.status = LessonSlotStatus.BOOKED.value
    booking.slot_id = new_slot.id
    booking.meeting_url = None
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise SlotUnavailableError("Слот уже занят") from exc

    updated = await _get_booking(session, booking.id)
    if updated is None:
        raise BookingNotFoundError("Запись не найдена")
    return booking_out_data(updated)


async def get_account_lessons(session: AsyncSession, user: User) -> AccountIndividualLessonsOut:
    packages = await session.scalars(
        select(LessonPackage)
        .where(LessonPackage.user_id == user.id)
        .options(selectinload(LessonPackage.offer))
        .order_by(LessonPackage.created_at.desc())
    )
    bookings = await session.scalars(
        select(LessonBooking)
        .where(LessonBooking.user_id == user.id)
        .options(
            selectinload(LessonBooking.package).selectinload(LessonPackage.offer),
            selectinload(LessonBooking.slot),
        )
        .order_by(LessonBooking.created_at.desc())
    )
    return AccountIndividualLessonsOut(
        packages=[package_out_data(package) for package in packages.all()],
        bookings=[booking_out_data(booking) for booking in bookings.all()],
    )
