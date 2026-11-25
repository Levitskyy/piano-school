from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class PurchasePaymentIn(BaseModel):
    offer_id: UUID
    slot_id: UUID
    promo_code: str | None = None
    payment_provider: Literal["yookassa", "prodamus"] = "yookassa"


class PurchasePaymentOut(BaseModel):
    order_id: UUID
    status: str
    total_minor: int
    discount_minor: int
    currency: str
    confirmation_url: str


class PaymentStatusOut(BaseModel):
    order_id: UUID
    status: str
    total_minor: int
    discount_minor: int
    currency: str
