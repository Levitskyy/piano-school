from datetime import UTC, datetime, timedelta
from uuid import UUID

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.individual_lessons import (
    IndividualLessonOffer,
    IndividualLessonOfferKind,
    LessonBooking,
    LessonPackage,
    LessonSlot,
    LessonSlotStatus,
)
from app.models.payments import PromoCode, PurchaseOrder, PurchaseOrderStatus
from app.models.user import User, UserRole


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

    def set_status(self, payment_id: str, status: str) -> None:
        self.payments[payment_id]["status"] = status

    async def __call__(
        self,
        method: str,
        path: str,
        *,
        body: dict | None = None,
        idempotence_key: str | None = None,
    ) -> dict:
        if method == "POST" and path.endswith("/cancel"):
            payment_id = path.split("/")[-2]
            self.payments[payment_id]["status"] = "canceled"
            return self.payments[payment_id]
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
        return self.payments[path.rsplit("/", 1)[-1]]


def payment_id_for(order: dict, fake: FakeYooKassa) -> str:
    return next(
        name
        for name, payment in fake.payments.items()
        if payment["metadata"]["order_id"] == order["order_id"]
    )


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


async def send_webhook(client: AsyncClient, payment_id: str, event: str) -> None:
    response = await client.post(
        "/payments/yookassa/webhook",
        json={"type": "notification", "event": event, "object": {"id": payment_id}},
    )
    assert response.status_code == 204, response.text


async def confirm(client: AsyncClient, order: dict, fake: FakeYooKassa) -> None:
    payment_id = payment_id_for(order, fake)
    fake.set_status(payment_id, "succeeded")
    await send_webhook(client, payment_id, "payment.succeeded")


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
    assert str(slot_one_id) not in {item["id"] for item in slots.json()}

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
        session.add(PromoCode(code="PERVIY", discount_percent=33.33, offer_id=single_id))
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


async def test_promo_code_does_not_apply_to_another_offer(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    fake = FakeYooKassa()
    monkeypatch.setattr("app.services.payments._yookassa", fake)
    single_id, package_id, one_id, _, two_id, _ = await seed_offers_and_slots(session_factory)
    async with session_factory() as session:
        session.add(PromoCode(code="BESPLATNO", discount_percent=100, offer_id=single_id))
        await session.commit()

    await client.post("/auth/register", json=register_payload)

    wrong_offer = await client.post(
        "/individual-lessons/purchase",
        json={
            "offer_id": str(package_id),
            "slot_id": str(one_id),
            "promo_code": "BESPLATNO",
        },
    )
    assert wrong_offer.status_code == 409

    async with session_factory() as session:
        promo = await session.scalar(select(PromoCode).where(PromoCode.code == "BESPLATNO"))
        assert promo is not None
        assert promo.used_at is None
        assert promo.reserved_order_id is None
        assert await session.scalar(select(PurchaseOrder)) is None

    right_offer = await purchase(client, single_id, one_id, "BESPLATNO")
    assert right_offer["total_minor"] == 0


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


async def test_pending_payment_keeps_slot_reserved(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    fake = FakeYooKassa()
    monkeypatch.setattr("app.services.payments._yookassa", fake)
    single_id, _, slot_one_id, _, _, _ = await seed_offers_and_slots(session_factory)
    await client.post("/auth/register", json=register_payload)

    order = await purchase(client, single_id, slot_one_id)
    payment_id = payment_id_for(order, fake)
    fake.set_status(payment_id, "pending")

    async with session_factory() as session:
        db_order = await session.get(PurchaseOrder, UUID(order["order_id"]))
        assert db_order is not None
        db_order.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        await session.commit()

    slots = await client.get("/individual-lessons/slots")
    assert str(slot_one_id) not in {item["id"] for item in slots.json()}

    async with session_factory() as session:
        db_order = await session.get(PurchaseOrder, UUID(order["order_id"]))
        assert db_order is not None
        assert db_order.status == PurchaseOrderStatus.PENDING.value
        assert db_order.expires_at.replace(tzinfo=UTC) > datetime.now(UTC)


async def test_late_payment_for_expired_order_books_slot(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    fake = FakeYooKassa()
    monkeypatch.setattr("app.services.payments._yookassa", fake)
    single_id, _, slot_one_id, _, _, _ = await seed_offers_and_slots(session_factory)
    await client.post("/auth/register", json=register_payload)

    order = await purchase(client, single_id, slot_one_id)
    payment_id = payment_id_for(order, fake)
    fake.set_status(payment_id, "succeeded")

    async with session_factory() as session:
        db_order = await session.get(PurchaseOrder, UUID(order["order_id"]))
        assert db_order is not None
        db_order.status = PurchaseOrderStatus.EXPIRED.value
        await session.commit()

    await send_webhook(client, payment_id, "payment.succeeded")

    account = await client.get("/individual-lessons/account")
    assert len(account.json()["bookings"]) == 1
    assert account.json()["bookings"][0]["status"] == "confirmed"

    status = await client.get(f"/payments/{order['order_id']}")
    assert status.json()["status"] == "succeeded"


async def test_late_payment_when_slot_is_taken_keeps_lesson_in_package(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    fake = FakeYooKassa()
    monkeypatch.setattr("app.services.payments._yookassa", fake)
    single_id, _, slot_one_id, _, _, _ = await seed_offers_and_slots(session_factory)

    await client.post("/auth/register", json=register_payload)
    order_a = await purchase(client, single_id, slot_one_id)
    payment_a = payment_id_for(order_a, fake)
    fake.set_status(payment_a, "succeeded")

    async with session_factory() as session:
        db_order = await session.get(PurchaseOrder, UUID(order_a["order_id"]))
        assert db_order is not None
        db_order.status = PurchaseOrderStatus.EXPIRED.value
        slot = await session.get(LessonSlot, slot_one_id)
        assert slot is not None
        slot.status = LessonSlotStatus.FREE.value
        await session.commit()

    client.cookies.clear()
    second_payload = {
        **register_payload,
        "name": "Борис",
        "email": "boris@example.com",
    }
    await client.post("/auth/register", json=second_payload)
    order_b = await purchase(client, single_id, slot_one_id)

    await send_webhook(client, payment_a, "payment.succeeded")

    async with session_factory() as session:
        user_a = await session.scalar(
            select(User).where(User.email == register_payload["email"])
        )
        assert user_a is not None
        packages = (
            await session.scalars(
                select(LessonPackage).where(LessonPackage.user_id == user_a.id)
            )
        ).all()
        bookings = (
            await session.scalars(
                select(LessonBooking).where(LessonBooking.user_id == user_a.id)
            )
        ).all()
    assert len(packages) == 1
    assert packages[0].remaining_lessons == 1
    assert bookings == []

    await confirm(client, order_b, fake)
    account_b = await client.get("/individual-lessons/account")
    assert len(account_b.json()["bookings"]) == 1


async def test_duplicate_webhook_is_idempotent(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    fake = FakeYooKassa()
    monkeypatch.setattr("app.services.payments._yookassa", fake)
    single_id, _, slot_one_id, _, _, _ = await seed_offers_and_slots(session_factory)
    await client.post("/auth/register", json=register_payload)

    order = await purchase(client, single_id, slot_one_id)
    await confirm(client, order, fake)
    await confirm(client, order, fake)

    account = await client.get("/individual-lessons/account")
    assert len(account.json()["packages"]) == 1
    assert len(account.json()["bookings"]) == 1


async def test_promo_code_is_reserved_for_pending_order(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    fake = FakeYooKassa()
    monkeypatch.setattr("app.services.payments._yookassa", fake)
    single_id, _, one_id, _, two_id, _ = await seed_offers_and_slots(session_factory)
    async with session_factory() as session:
        session.add(PromoCode(code="PERVIY", discount_percent=33.33, offer_id=single_id))
        await session.commit()

    await client.post("/auth/register", json=register_payload)
    order = await purchase(client, single_id, one_id, "PERVIY")

    second = await client.post(
        "/individual-lessons/purchase",
        json={
            "offer_id": str(single_id),
            "slot_id": str(two_id),
            "promo_code": "PERVIY",
        },
    )
    assert second.status_code == 409

    payment_id = payment_id_for(order, fake)
    fake.set_status(payment_id, "canceled")
    async with session_factory() as session:
        db_order = await session.get(PurchaseOrder, UUID(order["order_id"]))
        assert db_order is not None
        db_order.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        await session.commit()

    slots = await client.get("/individual-lessons/slots")
    assert str(one_id) in {item["id"] for item in slots.json()}

    order_again = await purchase(client, single_id, two_id, "PERVIY")
    assert order_again["discount_minor"] == 50_000


async def test_canceled_payment_releases_slot_and_promo(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    fake = FakeYooKassa()
    monkeypatch.setattr("app.services.payments._yookassa", fake)
    single_id, _, slot_one_id, _, _, _ = await seed_offers_and_slots(session_factory)
    async with session_factory() as session:
        session.add(PromoCode(code="PERVIY", discount_percent=33.33, offer_id=single_id))
        await session.commit()

    await client.post("/auth/register", json=register_payload)
    order = await purchase(client, single_id, slot_one_id, "PERVIY")
    payment_id = payment_id_for(order, fake)
    fake.set_status(payment_id, "canceled")

    await send_webhook(client, payment_id, "payment.canceled")

    status = await client.get(f"/payments/{order['order_id']}")
    assert status.json()["status"] == "cancelled"

    slots = await client.get("/individual-lessons/slots")
    assert str(slot_one_id) in {item["id"] for item in slots.json()}

    async with session_factory() as session:
        promo = await session.scalar(select(PromoCode).where(PromoCode.code == "PERVIY"))
        assert promo is not None
        assert promo.reserved_order_id is None
        assert promo.used_at is None


async def test_cancel_returns_lesson_to_package_and_frees_slot(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    fake = FakeYooKassa()
    monkeypatch.setattr("app.services.payments._yookassa", fake)
    single_id, _, _, _, _, slot_three_id = await seed_offers_and_slots(session_factory)
    await client.post("/auth/register", json=register_payload)

    order = await purchase(client, single_id, slot_three_id)
    await confirm(client, order, fake)

    account = await client.get("/individual-lessons/account")
    booking = account.json()["bookings"][0]
    assert booking["can_change"] is True
    package_id = booking["package_id"]

    cancelled = await client.post(f"/individual-lessons/bookings/{booking['id']}/cancel")
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "cancelled"

    account_after = await client.get("/individual-lessons/account")
    package = next(
        item for item in account_after.json()["packages"] if item["id"] == package_id
    )
    assert package["remaining_lessons"] == 1
    assert package["status"] == "active"

    slots = await client.get("/individual-lessons/slots")
    assert str(slot_three_id) in {item["id"] for item in slots.json()}

    rebooked = await client.post(
        "/individual-lessons/book",
        json={"package_id": package_id, "slot_id": str(slot_three_id)},
    )
    assert rebooked.status_code == 200, rebooked.text


async def test_student_cannot_cancel_too_late_but_teacher_can(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    fake = FakeYooKassa()
    monkeypatch.setattr("app.services.payments._yookassa", fake)
    single_id, _, _, _, _, _ = await seed_offers_and_slots(session_factory)

    now = datetime.now(UTC)
    near_start = now + timedelta(hours=1)
    async with session_factory() as session:
        near_slot = LessonSlot(
            starts_at=near_start,
            ends_at=near_start + timedelta(hours=1),
            duration_minutes=60,
        )
        session.add(near_slot)
        await session.commit()
        near_slot_id = near_slot.id

    await client.post("/auth/register", json=register_payload)
    order = await purchase(client, single_id, near_slot_id)
    await confirm(client, order, fake)

    account = await client.get("/individual-lessons/account")
    booking = account.json()["bookings"][0]
    assert booking["can_change"] is False

    rejected = await client.post(
        f"/individual-lessons/bookings/{booking['id']}/cancel"
    )
    assert rejected.status_code == 409

    teacher_payload = {
        "name": "Преподаватель",
        "email": "teacher@example.com",
        "password": "teacher-secret-123",
        "timezone": "Europe/Moscow",
    }
    assert (await client.post("/auth/register", json=teacher_payload)).status_code == 201
    async with session_factory() as session:
        teacher = await session.scalar(
            select(User).where(User.email == teacher_payload["email"])
        )
        assert teacher is not None
        teacher.role = UserRole.TEACHER.value
        await session.commit()

    login = await client.post(
        "/auth/login",
        json={
            "email": teacher_payload["email"],
            "password": teacher_payload["password"],
        },
    )
    assert login.status_code == 200

    cancelled = await client.post(f"/teacher/lessons/{booking['id']}/cancel")
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "cancelled"

    slots = await client.get("/individual-lessons/slots")
    assert str(near_slot_id) in {item["id"] for item in slots.json()}


async def test_reschedule_moves_booking_and_clears_meeting_url(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    fake = FakeYooKassa()
    monkeypatch.setattr("app.services.payments._yookassa", fake)
    _, package_offer_id, _, _, slot_two_id, slot_three_id = await seed_offers_and_slots(
        session_factory
    )
    await client.post("/auth/register", json=register_payload)

    order = await purchase(client, package_offer_id, slot_three_id)
    await confirm(client, order, fake)

    account = await client.get("/individual-lessons/account")
    booking = account.json()["bookings"][0]
    package_id = booking["package_id"]
    assert booking["can_change"] is True

    async with session_factory() as session:
        db_booking = await session.get(LessonBooking, UUID(booking["id"]))
        assert db_booking is not None
        db_booking.meeting_url = "https://meet.example.com/old"
        await session.commit()

    rescheduled = await client.post(
        f"/individual-lessons/bookings/{booking['id']}/reschedule",
        json={"slot_id": str(slot_two_id)},
    )
    assert rescheduled.status_code == 200, rescheduled.text
    assert rescheduled.json()["meeting_url"] is None
    assert rescheduled.json()["id"] == booking["id"]

    account_after = await client.get("/individual-lessons/account")
    moved = next(
        item for item in account_after.json()["bookings"] if item["id"] == booking["id"]
    )
    assert moved["starts_at"] != booking["starts_at"]

    package = next(
        item for item in account_after.json()["packages"] if item["id"] == package_id
    )
    assert package["remaining_lessons"] == 3

    slots = await client.get("/individual-lessons/slots")
    slot_ids = {item["id"] for item in slots.json()}
    assert str(slot_three_id) in slot_ids
    assert str(slot_two_id) not in slot_ids


async def test_student_cannot_cancel_another_students_booking(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    fake = FakeYooKassa()
    monkeypatch.setattr("app.services.payments._yookassa", fake)
    single_id, _, _, _, _, slot_three_id = await seed_offers_and_slots(session_factory)
    await client.post("/auth/register", json=register_payload)

    order = await purchase(client, single_id, slot_three_id)
    await confirm(client, order, fake)
    account = await client.get("/individual-lessons/account")
    booking_id = account.json()["bookings"][0]["id"]
    client.cookies.clear()
    second_payload = {
        **register_payload,
        "name": "Борис",
        "email": "boris@example.com",
    }
    await client.post("/auth/register", json=second_payload)

    forbidden = await client.post(f"/individual-lessons/bookings/{booking_id}/cancel")
    assert forbidden.status_code == 404

