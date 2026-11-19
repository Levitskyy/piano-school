from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class IndividualLessonOfferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    title: str
    description: str
    kind: str
    lessons_count: int
    duration_minutes: int
    price_minor: int | None
    currency: str
    validity_days: int | None


class LessonSlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    starts_at: datetime
    ends_at: datetime
    duration_minutes: int


class LessonPackageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    offer_slug: str
    offer_title: str
    total_lessons: int
    remaining_lessons: int
    status: str
    expires_at: datetime | None
    created_at: datetime


class LessonBookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    package_id: UUID
    offer_title: str
    status: str
    starts_at: datetime
    ends_at: datetime
    meeting_url: str | None
    created_at: datetime


class AccountIndividualLessonsOut(BaseModel):
    packages: list[LessonPackageOut]
    bookings: list[LessonBookingOut]


class PurchaseIndividualLessonIn(BaseModel):
    offer_id: UUID
    slot_id: UUID


class BookFromPackageIn(BaseModel):
    package_id: UUID
    slot_id: UUID


class PurchaseResultOut(BaseModel):
    booking: LessonBookingOut
    package: LessonPackageOut
