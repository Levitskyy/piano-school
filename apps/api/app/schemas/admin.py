from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OfferPriceIn(BaseModel):
    price: Decimal = Field(gt=0, le=Decimal("1000000"))


class PromoCodeIn(BaseModel):
    percent: Decimal = Field(gt=0, le=Decimal("100"))
    code: str | None = Field(default=None, max_length=32)


class PromoCodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    discount_percent: Decimal
    is_active: bool
    used_at: datetime | None
    created_at: datetime
