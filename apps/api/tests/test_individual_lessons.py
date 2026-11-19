from datetime import UTC, datetime, timedelta
from uuid import UUID

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.individual_lessons import (
    IndividualLessonOffer,
    IndividualLessonOfferKind,
    LessonSlot,
    LessonSlotStatus,
)


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
        )
        package = IndividualLessonOffer(
            slug="package-4",
            title="Пакет из 4 уроков",
            kind=IndividualLessonOfferKind.PACKAGE.value,
            lessons_count=4,
            duration_minutes=60,
            validity_days=180,
        )
        slot_one = LessonSlot(
            starts_at=base,
            ends_at=base + timedelta(hours=1),
            duration_minutes=60,
            status=LessonSlotStatus.FREE.value,
        )
        slot_same_day = LessonSlot(
            starts_at=base + timedelta(hours=2),
            ends_at=base + timedelta(hours=3),
            duration_minutes=60,
            status=LessonSlotStatus.FREE.value,
        )
        slot_two = LessonSlot(
            starts_at=base + timedelta(days=1),
            ends_at=base + timedelta(days=1, hours=1),
            duration_minutes=60,
            status=LessonSlotStatus.FREE.value,
        )
        slot_three = LessonSlot(
            starts_at=base + timedelta(days=2),
            ends_at=base + timedelta(days=2, hours=1),
            duration_minutes=60,
            status=LessonSlotStatus.FREE.value,
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


async def test_purchase_and_package_booking(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
) -> None:
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

    purchased = await client.post(
        "/individual-lessons/purchase",
        json={"offer_id": str(single_id), "slot_id": str(slot_one_id)},
    )
    assert purchased.status_code == 200
    body = purchased.json()
    assert body["package"]["remaining_lessons"] == 0
    assert body["booking"]["status"] == "confirmed"

    slots = await client.get("/individual-lessons/slots")
    assert {item["id"] for item in slots.json()} == {
        str(slot_two_id),
        str(slot_three_id),
    }

    same_day_conflict = await client.post(
        "/individual-lessons/purchase",
        json={"offer_id": str(package_id), "slot_id": str(slot_same_day_id)},
    )
    assert same_day_conflict.status_code == 409

    package_purchase = await client.post(
        "/individual-lessons/purchase",
        json={"offer_id": str(package_id), "slot_id": str(slot_two_id)},
    )
    assert package_purchase.status_code == 200
    package = package_purchase.json()["package"]

    booked = await client.post(
        "/individual-lessons/book",
        json={"package_id": package["id"], "slot_id": str(slot_three_id)},
    )
    assert booked.status_code == 200

    account = await client.get("/individual-lessons/account")
    assert account.status_code == 200
    data = account.json()
    assert len(data["bookings"]) == 3
    remaining = [item for item in data["packages"] if item["id"] == package["id"]][0]
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
