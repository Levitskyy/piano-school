from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.individual_lessons import IndividualLessonOfferOut

MAX_PRICE = Decimal("1000000")


class OfferPriceIn(BaseModel):
    price: Decimal = Field(gt=0, le=MAX_PRICE)


class OfferCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    slug: str | None = Field(default=None, max_length=80)
    description: str = Field(default="", max_length=2000)
    lessons_count: int = Field(ge=1, le=100)
    price: Decimal = Field(gt=0, le=MAX_PRICE)
    validity_days: int | None = Field(default=None, ge=1, le=3650)
    is_active: bool = True


class OfferUpdateIn(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    lessons_count: int | None = Field(default=None, ge=1, le=100)
    price: Decimal | None = Field(default=None, gt=0, le=MAX_PRICE)
    # None означает «очистить срок», отсутствие поля — «не менять».
    validity_days: int | None = Field(default=None, ge=1, le=3650)
    is_active: bool | None = None


class AdminOfferOut(IndividualLessonOfferOut):
    is_active: bool
    position: int


class PromoCodeIn(BaseModel):
    percent: Decimal = Field(gt=0, le=Decimal("100"))
    offer_slug: str = Field(min_length=1, max_length=80)
    code: str | None = Field(default=None, max_length=32)


class PromoCodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    discount_percent: Decimal
    offer_id: UUID | None
    is_active: bool
    used_at: datetime | None
    created_at: datetime
