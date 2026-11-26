import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from urllib.parse import parse_qs, urlparse
from uuid import UUID

from httpx import AsyncClient, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.individual_lessons import LessonPackage
from app.models.payments import (
    PaymentProvider,
    PromoCode,
    PurchaseOrder,
    PurchaseOrderStatus,
)
from app.models.user import User
from app.services.payments import prodamus_signature
from conftest import register_and_verify
from test_individual_lessons import YOOKASSA_WEBHOOK_HEADERS, seed_offers_and_slots

SECRET = "prodamus-test-secret"


def test_prodamus_signature_escapes_slashes() -> None:
    expected = hmac.new(
        SECRET.encode(),
        b'{"url":"https:\\/\\/site.test\\/success"}',
        hashlib.sha256,
    ).hexdigest()
    assert prodamus_signature({"url": "https://site.test/success"}, SECRET) == expected


class SettingsStub:
    prodamus_secret_key = SECRET
    prodamus_form_url = "https://payform.test/"
    prodamus_payment_method = "monetaworld"
    prodamus_currency = "rub"
    prodamus_success_url = "https://site.test"
    payment_reservation_minutes = 15
    yookassa_shop_id = ""
    yookassa_secret_key = ""


def use_prodamus(monkeypatch) -> None:
    monkeypatch.setattr("app.services.payments.get_settings", lambda: SettingsStub())


async def purchase(
    client: AsyncClient,
    offer_id: UUID,
    slot_id: UUID,
    promo_code: str | None = None,
) -> dict:
    response = await client.post(
        "/individual-lessons/purchase",
        json={
            "offer_id": str(offer_id),
            "slot_id": str(slot_id),
            "promo_code": promo_code,
            "payment_provider": "prodamus",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


async def send_webhook(
    client: AsyncClient,
    order_id: str,
    *,
    amount: str = "1500.00",
    status: str = "success",
    internal_id: str = "12345",
    currency: str = "rub",
    secret: str = SECRET,
) -> Response:
    values = {
        "order_id": internal_id,
        "order_num": order_id,
        "payment_status": status,
        "sum": amount,
        "currency": currency,
        "products": [
            {"name": "Разовый урок", "price": amount, "quantity": "1"},
        ],
    }
    return await client.post(
        "/payments/prodamus/webhook",
        json={"submit": json.dumps(values, ensure_ascii=False)},
        headers={"sign": prodamus_signature(values, secret)},
    )


async def packages_count(client: AsyncClient) -> int:
    response = await client.get("/individual-lessons/account")
    assert response.status_code == 200, response.text
    return len(response.json()["packages"])


async def test_prodamus_purchase_creates_signed_link_without_granting_access(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    use_prodamus(monkeypatch)
    single_id, _, slot_one_id, _, _, _ = await seed_offers_and_slots(session_factory)
    await register_and_verify(client, session_factory, register_payload)

    order = await purchase(client, single_id, slot_one_id)

    url = urlparse(order["confirmation_url"])
    query = parse_qs(url.query)
    assert url.scheme == "https"
    assert url.netloc == "payform.test"
    assert query["do"] == ["pay"]
    assert query["callbackType"] == ["json"]
    assert query["payment_method"] == ["monetaworld"]
    assert query["currency"] == ["rub"]
    assert query["urlSuccess"] == [
        f"https://site.test/payment/success?order_num={order['order_id']}"
    ]
    assert query["order_id"] == [order["order_id"]]
    assert query["customer_email"] == [register_payload["email"]]
    assert query["products[0][price]"] == ["1500.00"]

    signed = {
        "do": query["do"][0],
        "callbackType": query["callbackType"][0],
        "order_id": query["order_id"][0],
        "customer_email": query["customer_email"][0],
        "payment_method": query["payment_method"][0],
        "currency": query["currency"][0],
        "urlSuccess": query["urlSuccess"][0],
        "products": [
            {
                "name": query["products[0][name]"][0],
                "sku": query["products[0][sku]"][0],
                "price": query["products[0][price]"][0],
                "quantity": query["products[0][quantity]"][0],
            }
        ],
    }
    assert query["signature"] == [prodamus_signature(signed, SECRET)]

    assert await packages_count(client) == 0
    async with session_factory() as session:
        db_order = await session.get(PurchaseOrder, UUID(order["order_id"]))
        assert db_order is not None
        assert db_order.provider == PaymentProvider.PRODAMUS.value
        assert db_order.status == PurchaseOrderStatus.PENDING.value
        assert db_order.provider_payment_id is None


async def test_signed_prodamus_webhook_grants_lesson_and_is_idempotent(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    use_prodamus(monkeypatch)
    single_id, _, slot_one_id, _, _, _ = await seed_offers_and_slots(session_factory)
    await register_and_verify(client, session_factory, register_payload)
    order = await purchase(client, single_id, slot_one_id)

    first = await send_webhook(client, order["order_id"])
    assert first.status_code == 200, first.text
    assert first.text == "OK"

    account = (await client.get("/individual-lessons/account")).json()
    assert len(account["packages"]) == 1
    assert account["packages"][0]["total_lessons"] == 1
    assert account["packages"][0]["remaining_lessons"] == 0
    assert len(account["bookings"]) == 1

    status = await client.get(f"/payments/{order['order_id']}")
    assert status.json()["status"] == "succeeded"

    second = await send_webhook(client, order["order_id"], internal_id="99999")
    assert second.status_code == 200, second.text
    assert await packages_count(client) == 1

    async with session_factory() as session:
        db_order = await session.get(PurchaseOrder, UUID(order["order_id"]))
        assert db_order is not None
        assert db_order.provider_payment_id == "12345"
        assert db_order.status == PurchaseOrderStatus.SUCCEEDED.value
        package = await session.scalar(
            select(LessonPackage).where(LessonPackage.user_id == db_order.user_id)
        )
        assert package is not None


async def test_prodamus_webhook_rejects_bad_signature(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    use_prodamus(monkeypatch)
    single_id, _, slot_one_id, _, _, _ = await seed_offers_and_slots(session_factory)
    await register_and_verify(client, session_factory, register_payload)
    order = await purchase(client, single_id, slot_one_id)

    forged = await send_webhook(client, order["order_id"], secret="wrong-secret")
    assert forged.status_code == 400

    assert await packages_count(client) == 0
    async with session_factory() as session:
        db_order = await session.get(PurchaseOrder, UUID(order["order_id"]))
        assert db_order is not None
        assert db_order.status == PurchaseOrderStatus.PENDING.value


async def test_prodamus_webhook_rejects_wrong_amount_currency_and_order(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    use_prodamus(monkeypatch)
    single_id, _, slot_one_id, _, _, _ = await seed_offers_and_slots(session_factory)
    await register_and_verify(client, session_factory, register_payload)
    order = await purchase(client, single_id, slot_one_id)

    wrong_amount = await send_webhook(client, order["order_id"], amount="1.00")
    assert wrong_amount.status_code == 400

    wrong_currency = await send_webhook(client, order["order_id"], currency="usd")
    assert wrong_currency.status_code == 400

    unknown_order = await send_webhook(client, "00000000-0000-4000-8000-000000000000")
    assert unknown_order.status_code == 200

    assert await packages_count(client) == 0


async def test_prodamus_webhook_waits_for_success_status(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    use_prodamus(monkeypatch)
    single_id, _, slot_one_id, _, _, _ = await seed_offers_and_slots(session_factory)
    await register_and_verify(client, session_factory, register_payload)
    order = await purchase(client, single_id, slot_one_id)

    failed = await send_webhook(client, order["order_id"], status="fail")
    assert failed.status_code == 200
    assert await packages_count(client) == 0

    success = await send_webhook(client, order["order_id"])
    assert success.status_code == 200
    assert await packages_count(client) == 1


async def test_expired_prodamus_order_still_accepts_late_payment(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    use_prodamus(monkeypatch)
    single_id, _, slot_one_id, _, _, _ = await seed_offers_and_slots(session_factory)
    await register_and_verify(client, session_factory, register_payload)
    order = await purchase(client, single_id, slot_one_id)

    async with session_factory() as session:
        db_order = await session.get(PurchaseOrder, UUID(order["order_id"]))
        assert db_order is not None
        db_order.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        await session.commit()

    response = await send_webhook(client, order["order_id"])
    assert response.status_code == 200, response.text
    assert await packages_count(client) == 1


async def test_promo_discount_is_signed_and_required_in_webhook(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    use_prodamus(monkeypatch)
    single_id, _, slot_one_id, _, _, _ = await seed_offers_and_slots(session_factory)
    await register_and_verify(client, session_factory, register_payload)

    async with session_factory() as session:
        user = await session.scalar(
            select(User).where(User.email == register_payload["email"])
        )
        assert user is not None
        session.add(
            PromoCode(
                code="PERVIY",
                discount_percent=Decimal("33.33"),
                offer_id=single_id,
                is_active=True,
            )
        )
        await session.commit()

    order = await purchase(client, single_id, slot_one_id, "perviy")
    query = parse_qs(urlparse(order["confirmation_url"]).query)
    assert query["products[0][price]"] == ["1000.00"]
    assert order["total_minor"] == 100_000

    full_price = await send_webhook(client, order["order_id"])
    assert full_price.status_code == 400

    discounted = await send_webhook(client, order["order_id"], amount="1000.00")
    assert discounted.status_code == 200, discounted.text
    assert await packages_count(client) == 1


async def test_yookassa_webhook_cannot_confirm_prodamus_order(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    use_prodamus(monkeypatch)
    single_id, _, slot_one_id, _, _, _ = await seed_offers_and_slots(session_factory)
    await register_and_verify(client, session_factory, register_payload)
    await purchase(client, single_id, slot_one_id)

    response = await client.post(
        "/payments/yookassa/webhook",
        json={
            "type": "notification",
            "event": "payment.succeeded",
            "object": {"id": "12345"},
        },
        headers=YOOKASSA_WEBHOOK_HEADERS,
    )
    assert response.status_code == 204
    assert await packages_count(client) == 0
