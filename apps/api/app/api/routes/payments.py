from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db import get_session
from app.models.user import User
from app.schemas.payments import PaymentStatusOut
from app.services import payments as payments_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/yookassa/webhook", status_code=status.HTTP_204_NO_CONTENT)
async def yookassa_webhook(
    payload: dict,
    session: AsyncSession = Depends(get_session),
) -> Response:
    payment = payload.get("object") or {}
    payment_id = payment.get("id")
    if not isinstance(payment_id, str) or not payment_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Некорректное уведомление",
        )

    try:
        await payments_service.confirm_payment(session, payment_id)
    except payments_service.PaymentError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{order_id}", response_model=PaymentStatusOut)
async def payment_status(
    order_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PaymentStatusOut:
    try:
        order_uuid = UUID(order_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден",
        ) from exc

    order = await payments_service.get_user_order(session, order_uuid, user)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
    return PaymentStatusOut(
        order_id=order.id,
        status=order.status,
        total_minor=order.total_minor,
        discount_minor=order.discount_minor,
        currency=order.currency,
    )
