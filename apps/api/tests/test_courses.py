from datetime import UTC, datetime
from uuid import UUID

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.course import (
    Course,
    CourseAccess,
    CourseModule,
    CourseOffer,
    CourseStatus,
    Lesson,
    LessonMaterial,
    LessonStatus,
    OfferKind,
    VideoStatus,
)


async def create_course(
    session_factory: async_sessionmaker[AsyncSession],
) -> Course:
    async with session_factory() as session:
        course = Course(
            slug="fortepiano",
            title="Фортепиано",
            subtitle="Первый семестр",
            description="Спокойный курс.",
            status=CourseStatus.PUBLISHED.value,
        )
        course.offers.extend(
            [
                CourseOffer(
                    slug="self-study",
                    title="Самостоятельно",
                    kind=OfferKind.SELF_STUDY.value,
                ),
                CourseOffer(
                    slug="with-mentorship",
                    title="С сопровождением",
                    kind=OfferKind.WITH_MENTORSHIP.value,
                    mentorship_days=90,
                ),
            ]
        )
        module = CourseModule(title="Посадка и звук", position=1)
        lesson = Lesson(
            slug="posadka",
            title="Посадка",
            description="Первый урок.",
            position=1,
            status=LessonStatus.PUBLISHED.value,
            video_status=VideoStatus.PENDING.value,
        )
        lesson.materials.append(
            LessonMaterial(title="Ноты", kind="pdf", url="https://example.com/notes.pdf")
        )
        module.lessons.append(lesson)
        course.modules.append(module)
        session.add(course)
        await session.commit()
        return course


async def test_public_catalog_and_course(
    client: AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await create_course(session_factory)

    catalog = await client.get("/courses")
    assert catalog.status_code == 200
    assert catalog.json()[0]["slug"] == "fortepiano"
    assert len(catalog.json()[0]["offers"]) == 2

    detail = await client.get("/courses/fortepiano")
    assert detail.status_code == 200
    body = detail.json()
    assert body["modules"][0]["lessons"][0]["slug"] == "posadka"
    assert "materials" not in body["modules"][0]["lessons"][0]


async def test_lesson_requires_auth_and_access(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
) -> None:
    course = await create_course(session_factory)

    unauthorized = await client.get("/courses/fortepiano/lessons/posadka")
    assert unauthorized.status_code == 401

    registered = await client.post("/auth/register", json=register_payload)
    assert registered.status_code == 201
    user_id = UUID(registered.json()["id"])

    no_access = await client.get("/courses/fortepiano/lessons/posadka")
    assert no_access.status_code == 403

    async with session_factory() as session:
        session.add(
            CourseAccess(
                user_id=user_id,
                course_id=course.id,
                offer_id=course.offers[0].id,
                source="manual",
                starts_at=datetime.now(UTC),
            )
        )
        await session.commit()

    lesson = await client.get("/courses/fortepiano/lessons/posadka")
    assert lesson.status_code == 200
    assert lesson.json()["materials"][0]["title"] == "Ноты"

    progress = await client.patch(
        "/courses/fortepiano/lessons/posadka/progress",
        json={"status": "completed", "last_position_seconds": 120},
    )
    assert progress.status_code == 200
    assert progress.json()["status"] == "completed"

    account = await client.get("/account/courses")
    assert account.status_code == 200
    assert account.json()[0]["completed_lessons"] == 1
    assert account.json()[0]["total_lessons"] == 1


async def test_draft_course_is_hidden(
    client: AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    async with session_factory() as session:
        session.add(
            Course(
                slug="draft",
                title="Черновик",
                status=CourseStatus.DRAFT.value,
            )
        )
        await session.commit()

    catalog = await client.get("/courses")
    assert catalog.status_code == 200
    assert catalog.json() == []

    detail = await client.get("/courses/draft")
    assert detail.status_code == 404
