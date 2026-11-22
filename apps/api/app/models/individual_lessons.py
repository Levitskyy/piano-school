from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.user import User


def utcnow() -> datetime:
    return datetime.now(UTC)


class IndividualLessonOfferKind(StrEnum):
    SINGLE = "single"
    PACKAGE = "package"


class LessonSlotStatus(StrEnum):
    FREE = "free"
    BOOKED = "booked"
    BLOCKED = "blocked"


class LessonPackageStatus(StrEnum):
    ACTIVE = "active"
    EXHAUSTED = "exhausted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class LessonBookingStatus(StrEnum):
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class IndividualLessonOffer(Base):
    __tablename__ = "individual_lesson_offers"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    kind: Mapped[str] = mapped_column(
        String(20), default=IndividualLessonOfferKind.SINGLE.value, index=True
    )
    lessons_count: Mapped[int] = mapped_column(Integer, default=1)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    price_minor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    validity_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    packages: Mapped[list[LessonPackage]] = relationship(back_populates="offer")


class LessonSlot(Base):
    __tablename__ = "lesson_slots"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), unique=True, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    status: Mapped[str] = mapped_column(String(20), default=LessonSlotStatus.FREE.value, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    booking: Mapped[LessonBooking | None] = relationship(back_populates="slot", uselist=False)


class LessonPackage(Base):
    __tablename__ = "lesson_packages"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    offer_id: Mapped[UUID] = mapped_column(
        ForeignKey("individual_lesson_offers.id", ondelete="RESTRICT"), index=True
    )
    total_lessons: Mapped[int] = mapped_column(Integer)
    remaining_lessons: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        String(20), default=LessonPackageStatus.ACTIVE.value, index=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    user: Mapped[User] = relationship()
    offer: Mapped[IndividualLessonOffer] = relationship(back_populates="packages")
    bookings: Mapped[list[LessonBooking]] = relationship(
        back_populates="package", cascade="all, delete-orphan"
    )


class LessonBooking(Base):
    __tablename__ = "lesson_bookings"
    __table_args__ = (
        Index(
            "uq_lesson_bookings_confirmed_slot_id",
            "slot_id",
            unique=True,
            postgresql_where=text("status = 'confirmed'"),
            sqlite_where=text("status = 'confirmed'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    package_id: Mapped[UUID] = mapped_column(
        ForeignKey("lesson_packages.id", ondelete="CASCADE"), index=True
    )
    slot_id: Mapped[UUID] = mapped_column(
        ForeignKey("lesson_slots.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default=LessonBookingStatus.CONFIRMED.value, index=True
    )
    meeting_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        server_default=func.now(),
    )

    user: Mapped[User] = relationship()
    package: Mapped[LessonPackage] = relationship(back_populates="bookings")
    slot: Mapped[LessonSlot] = relationship(back_populates="booking")
