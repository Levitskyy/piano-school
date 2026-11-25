from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.individual_lessons import (
    IndividualLessonOffer,
    LessonSlot,
    LessonSlotStatus,
)
from app.models.user import User, UserRole
from conftest import register_and_verify


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
                "amount": body["amount"],
                "metadata": body["metadata"],
            }
            return {
                "id": payment_id,
                "confirmation": {"confirmation_url": "https://yookassa.test/pay"},
            }
        return {**self.payments[path.rsplit("/", 1)[-1]], "status": "succeeded"}


async def test_teacher_views_bookings_and_sets_meeting_url(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
    monkeypatch,
) -> None:
    now = datetime.now(UTC)
    starts_at = (now + timedelta(days=1)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )
    async with session_factory() as session:
        offer = IndividualLessonOffer(
            slug="single",
            title="Разовый урок",
            lessons_count=1,
            duration_minutes=60,
            price_minor=150_000,
        )
        slot = LessonSlot(
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=1),
            duration_minutes=60,
            status=LessonSlotStatus.FREE.value,
        )
        session.add_all([offer, slot])
        await session.commit()
        offer_id = offer.id
        slot_id = slot.id

    fake = FakeYooKassa()
    monkeypatch.setattr("app.services.payments._yookassa", fake)

    await register_and_verify(client, session_factory, register_payload)
    student_cookies = dict(client.cookies)

    purchased = await client.post(
        "/individual-lessons/purchase",
        json={"offer_id": str(offer_id), "slot_id": str(slot_id)},
    )
    assert purchased.status_code == 200, purchased.text
    payment_id = next(
        name
        for name, payment in fake.payments.items()
        if payment["metadata"]["order_id"] == purchased.json()["order_id"]
    )
    webhook = await client.post(
        "/payments/yookassa/webhook",
        json={"type": "notification", "object": {"id": payment_id}},
    )
    assert webhook.status_code == 204, webhook.text

    account = await client.get("/individual-lessons/account")
    assert account.status_code == 200
    booking_id = account.json()["bookings"][0]["id"]

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
    assert login.json()["role"] == "teacher"
    teacher_cookies = dict(client.cookies)

    client.cookies.clear()
    client.cookies.update(student_cookies)
    forbidden = await client.get("/teacher/lessons")
    assert forbidden.status_code == 403

    client.cookies.clear()
    client.cookies.update(teacher_cookies)
    lessons = await client.get("/teacher/lessons")
    assert lessons.status_code == 200
    data = lessons.json()
    assert len(data) == 1
    assert data[0]["id"] == booking_id
    assert data[0]["student_email"] == register_payload["email"]
    assert data[0]["meeting_url"] is None

    updated = await client.patch(
        f"/teacher/lessons/{booking_id}",
        json={"meeting_url": "https://meet.example.com/lesson-1"},
    )
    assert updated.status_code == 200
    assert updated.json()["meeting_url"] == "https://meet.example.com/lesson-1"

    client.cookies.clear()
    client.cookies.update(student_cookies)
    account = await client.get("/individual-lessons/account")
    assert account.status_code == 200
    student_booking = account.json()["bookings"][0]
    assert student_booking["meeting_url"] == "https://meet.example.com/lesson-1"
