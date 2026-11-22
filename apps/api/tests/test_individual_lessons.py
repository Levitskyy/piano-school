from datetime import UTC, datetime, timedelta
from uuid import UUID

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.individual_lessons import (
    IndividualLessonOffer,
    IndividualLessonOfferKind,
    LessonSlot,
)
from app.models.payments import PromoCode


async def seed_offers_and_slots(
    session_factory: async_sessionmaker[AsyncSession],
) -> tuple[UUID, UUID, UUID, UUID, UUID, UUID]:
    now = datetime.now(UTC)
    base = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    async with session_factory() as session:
        single = IndividualLessonOffer(
            slug="single",
            title="Разовый урок",
            kind=IndividualLessonOfferKind.SINGLE.value,
            lessons_count=1,
            duration_minutes=60,
            price_minor=150_000,
        )
        package = IndividualLessonOffer(
            slug="package-4",
            title="Пакет из 4 уроков",
            kind=IndividualLessonOfferKind.PACKAGE.value,
            lessons_count=4,
            duration_minutes=60,
            validity_days=180,
            price_minor=500_000,
        )
        slot_one = LessonSlot(
            starts_at=base,
            ends_at=base + timedelta(hours=1),
            duration_minutes=60,
        )
        slot_same_day = LessonSlot(
            starts_at=base + timedelta(hours=2),
            ends_at=base + timedelta(hours=3),
            duration_minutes=60,
        )
        slot_two = LessonSlot(
            starts_at=base + timedelta(days=1),
            ends_at=base + timedelta(days=1, hours=1),
            duration_minutes=60,
        )
        slot_three = LessonSlot(
            starts_at=base + timedelta(days=2),
            ends_at=base + timedelta(days=2, hours=1),
            duration_minutes=60,
        )
        session.add_all(
            [single, package, slot_one, slot_same_day, slot_two, slot_three]
        )
        await session.commit()
        return (
            single.id,
            package.id,
            slot_one.id,
            slot_same_day.id,
            slot_two.id,
            slot_three.id,
        )


class FakeYooKassa:
    def __init__(self) -> None:
        self.payments: dict[str, dict] = {}

    async def __call__(
        self,
        method: str,
        path: str,
        *,
        body: dict | None = None,
        idempotence_key: str | None = None,
    ) -> dict:
        if method == "POST":
            payment_id = f"pay-{len(self.payments) + 1}"
            self.payments[payment_id] = {
                "status": "pending",
                "amount": body["amount"],
                "metadata": body["metadata"],
            }
            return {
                "id": payment_id,
                "confirmation": {"confirmation_url": "https://yookassa.test/pay"},
            }
        payment = self.payments[path.rsplit("/", 1)[-1]]
        return {**payment, "status": "succeeded"}


async def purchase(
    client: AsyncClient, offer_id: UUID, slot_id: UUID, promo_code: str | None = None
) -> dict:
    response = await client.post(
        "/individual-lessons/purchase",
        json={
            "offer_id": str(offer_id),
            "slot_id": str(slot_id),
            "promo_code": promo_code,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


async def confirm(client: AsyncClient, order: dict, fake: FakeYooKassa) -> None:
    payment_id = next(
        name
        for name, payment in fake.payments.items()
        if payment["metadata"]["order_id"] == order["order_id"]
    )
    response = await client.post(
        "/payments/yookassa/webhook", json={"type": "notification", "object": {"id": payment_id}}
    )
    assert response.status_code == 204, response.text


async def test_offers_and_slots_are_public(
    client: AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await seed_offers_and_slots(session_factory)

    offers = await client.get("/individual-lessons/offers")
    assert offers.status_code == 200
    assert [item["slug"] for item in offers.json()] == ["single", "package-4"]

    slots = await client.get("/individual-lessons/slots")
    assert slots.status_code == 200
    assert len(slots.json()) == 4


async def test_purchase_requires_payment_before_booking(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    fake = FakeYooKassa()
    monkeypatch.setattr("app.services.payments._yookassa", fake)
    (
        single_id,
        package_id,
        slot_one_id,
        slot_same_day_id,
        slot_two_id,
        slot_three_id,
    ) = await seed_offers_and_slots(session_factory)

    unauthorized = await client.post(
        "/individual-lessons/purchase",
        json={"offer_id": str(single_id), "slot_id": str(slot_one_id)},
    )
    assert unauthorized.status_code == 401

    registered = await client.post("/auth/register", json=register_payload)
    assert registered.status_code == 201

    order = await purchase(client, single_id, slot_one_id)
    assert order["status"] == "pending"
    assert order["total_minor"] == 150_000

    account_before = await client.get("/individual-lessons/account")
    assert account_before.json()["bookings"] == []

    slots = await client.get("/individual-lessons/slots")
    assert slot_one_id not in {item["id"] for item in slots.json()}

    await confirm(client, order, fake)

    account_after = await client.get("/individual-lessons/account")
    assert len(account_after.json()["bookings"]) == 1
    assert account_after.json()["bookings"][0]["status"] == "confirmed"

    same_day_conflict = await client.post(
        "/individual-lessons/purchase",
        json={"offer_id": str(package_id), "slot_id": str(slot_same_day_id)},
    )
    assert same_day_conflict.status_code == 409

    package_order = await purchase(client, package_id, slot_two_id)
    await confirm(client, package_order, fake)
    package = (await client.get("/individual-lessons/account")).json()["packages"][0]

    booked = await client.post(
        "/individual-lessons/book",
        json={"package_id": package["id"], "slot_id": str(slot_three_id)},
    )
    assert booked.status_code == 200

    account = await client.get("/individual-lessons/account")
    assert len(account.json()["bookings"]) == 3
    remaining = [item for item in account.json()["packages"] if item["id"] == package["id"]][0]
    assert remaining["remaining_lessons"] == 2

    foreign_booking = await client.post(
        "/individual-lessons/book",
        json={"package_id": package["id"], "slot_id": str(slot_three_id)},
    )
    assert foreign_booking.status_code == 409

    conflict = await client.post(
        "/individual-lessons/purchase",
        json={"offer_id": str(package_id), "slot_id": str(slot_one_id)},
    )
    assert conflict.status_code == 409


async def test_one_time_promo_code_discounts_payment(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    fake = FakeYooKassa()
    monkeypatch.setattr("app.services.payments._yookassa", fake)
    single_id, _, one_id, _, two_id, _ = await seed_offers_and_slots(session_factory)
    async with session_factory() as session:
        session.add(PromoCode(code="PERVIY", discount_percent=33.33))
        await session.commit()

    await client.post("/auth/register", json=register_payload)

    order = await purchase(client, single_id, one_id, " perviy ")
    assert order["discount_minor"] == 50_000
    assert order["total_minor"] == 100_000
    await confirm(client, order, fake)

    reused = await client.post(
        "/individual-lessons/purchase",
        json={
            "offer_id": str(single_id),
            "slot_id": str(two_id),
            "promo_code": "PERVIY",
        },
    )
    assert reused.status_code == 409


async def test_courses_are_hidden_by_flag(
    client: AsyncClient,
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    class SettingsStub:
        courses_enabled = False

    monkeypatch.setattr(
        "app.api.routes.account.get_settings", lambda: SettingsStub()
    )
    await client.post("/auth/register", json=register_payload)

    assert (await client.get("/account/courses")).status_code == 404
