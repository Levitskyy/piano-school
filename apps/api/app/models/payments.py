from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.individual_lessons import IndividualLessonOffer, LessonSlot
from app.models.user import User


def utcnow() -> datetime:
    return datetime.now(UTC)


class PurchaseOrderStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    orders: Mapped[list[PurchaseOrder]] = relationship(back_populates="promo_code")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    offer_id: Mapped[UUID] = mapped_column(
        ForeignKey("individual_lesson_offers.id", ondelete="RESTRICT"), index=True
    )
    slot_id: Mapped[UUID] = mapped_column(
        ForeignKey("lesson_slots.id", ondelete="RESTRICT"), index=True
    )
    promo_code_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("promo_codes.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    price_minor: Mapped[int] = mapped_column(Integer)
    discount_minor: Mapped[int] = mapped_column(Integer, default=0)
    total_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    status: Mapped[str] = mapped_column(
        String(20), default=PurchaseOrderStatus.PENDING.value, index=True
    )
    yookassa_payment_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
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
    offer: Mapped[IndividualLessonOffer] = relationship()
    slot: Mapped[LessonSlot] = relationship()
    promo_code: Mapped[PromoCode | None] = relationship(back_populates="orders")
