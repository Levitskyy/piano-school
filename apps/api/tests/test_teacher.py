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


async def test_teacher_views_bookings_and_sets_meeting_url(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
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

    registered = await client.post("/auth/register", json=register_payload)
    assert registered.status_code == 201
    student_cookies = dict(client.cookies)

    purchased = await client.post(
        "/individual-lessons/purchase",
        json={"offer_id": str(offer_id), "slot_id": str(slot_id)},
    )
    assert purchased.status_code == 200
    booking_id = purchased.json()["booking"]["id"]

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
