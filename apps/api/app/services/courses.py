from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.course import (
    Course,
    CourseAccess,
    CourseModule,
    CourseOffer,
    CourseStatus,
    Lesson,
    LessonProgress,
    LessonStatus,
    ProgressStatus,
)
from app.models.user import User
from app.schemas.course import (
    AccountCourseOut,
    CourseAccessOut,
    CourseOfferOut,
    CourseOut,
    CourseSummaryOut,
    LessonDetailOut,
    LessonMaterialOut,
    LessonSummaryOut,
    ModuleOut,
    ProgressOut,
    ProgressUpdateIn,
)


def _offer_out(offer: CourseOffer) -> CourseOfferOut:
    return CourseOfferOut.model_validate(offer)


def course_summary_out(course: Course) -> CourseSummaryOut:
    return CourseSummaryOut(
        id=course.id,
        slug=course.slug,
        title=course.title,
        subtitle=course.subtitle,
        description=course.description,
        level=course.level,
        cover_url=course.cover_url,
        offers=[_offer_out(offer) for offer in course.offers if offer.is_active],
    )


def course_out(course: Course) -> CourseOut:
    modules: list[ModuleOut] = []
    for module in course.modules:
        lessons = [
            LessonSummaryOut.model_validate(lesson)
            for lesson in module.lessons
            if lesson.status == LessonStatus.PUBLISHED.value
        ]
        if lessons:
            modules.append(
                ModuleOut(
                    id=module.id,
                    title=module.title,
                    description=module.description,
                    position=module.position,
                    lessons=lessons,
                )
            )

    summary = course_summary_out(course)
    return CourseOut(**summary.model_dump(), modules=modules)


def _progress_out(progress: LessonProgress | None) -> ProgressOut | None:
    if progress is None:
        return None
    return ProgressOut(
        status=progress.status,
        last_position_seconds=progress.last_position_seconds,
        completed_at=progress.completed_at,
    )


async def list_published_courses(session: AsyncSession) -> list[Course]:
    result = await session.scalars(
        select(Course)
        .where(Course.status == CourseStatus.PUBLISHED.value)
        .options(selectinload(Course.offers))
        .order_by(Course.position, Course.created_at)
    )
    return list(result)


async def get_published_course(session: AsyncSession, slug: str) -> Course | None:
    return await session.scalar(
        select(Course)
        .where(
            Course.slug == slug,
            Course.status == CourseStatus.PUBLISHED.value,
        )
        .options(
            selectinload(Course.offers),
            selectinload(Course.modules).selectinload(CourseModule.lessons),
        )
    )


async def get_active_access(
    session: AsyncSession, user_id: UUID, course_id: UUID
) -> CourseAccess | None:
    now = datetime.now(UTC)
    return await session.scalar(
        select(CourseAccess)
        .where(
            CourseAccess.user_id == user_id,
            CourseAccess.course_id == course_id,
            CourseAccess.starts_at <= now,
            or_(
                CourseAccess.expires_at.is_(None),
                CourseAccess.expires_at > now,
            ),
        )
        .order_by(CourseAccess.created_at.desc())
        .limit(1)
    )


async def get_published_lesson(
    session: AsyncSession, course_slug: str, lesson_slug: str
) -> Lesson | None:
    return await session.scalar(
        select(Lesson)
        .join(Lesson.module)
        .join(CourseModule.course)
        .where(
            Course.slug == course_slug,
            Course.status == CourseStatus.PUBLISHED.value,
            Lesson.slug == lesson_slug,
            Lesson.status == LessonStatus.PUBLISHED.value,
        )
        .options(
            selectinload(Lesson.materials),
            selectinload(Lesson.module).selectinload(CourseModule.course),
        )
    )


async def get_lesson_detail(
    session: AsyncSession, user: User, course_slug: str, lesson_slug: str
) -> LessonDetailOut | None:
    lesson = await get_published_lesson(session, course_slug, lesson_slug)
    if lesson is None:
        return None

    course = lesson.module.course
    access = await get_active_access(session, user.id, course.id)
    if access is None:
        raise PermissionError("Нет доступа к уроку")

    progress = await session.scalar(
        select(LessonProgress).where(
            LessonProgress.user_id == user.id,
            LessonProgress.lesson_id == lesson.id,
        )
    )

    return LessonDetailOut(
        id=lesson.id,
        slug=lesson.slug,
        title=lesson.title,
        description=lesson.description,
        duration_seconds=lesson.duration_seconds,
        module_title=lesson.module.title,
        course_slug=course.slug,
        course_title=course.title,
        materials=[
            LessonMaterialOut.model_validate(material)
            for material in lesson.materials
        ],
        progress=_progress_out(progress),
    )


async def list_account_courses(
    session: AsyncSession, user: User
) -> list[AccountCourseOut]:
    now = datetime.now(UTC)
    accesses = list(
        await session.scalars(
            select(CourseAccess)
            .where(
                CourseAccess.user_id == user.id,
                CourseAccess.starts_at <= now,
                or_(
                    CourseAccess.expires_at.is_(None),
                    CourseAccess.expires_at > now,
                ),
            )
            .options(
                selectinload(CourseAccess.course).selectinload(Course.offers),
                selectinload(CourseAccess.offer),
            )
            .order_by(CourseAccess.created_at.desc())
        )
    )

    result: list[AccountCourseOut] = []
    for access in accesses:
        lesson_ids = select(Lesson.id).join(CourseModule).where(
            CourseModule.course_id == access.course_id,
            Lesson.status == LessonStatus.PUBLISHED.value,
        )
        total = (
            await session.scalar(
                select(func.count()).select_from(lesson_ids.subquery())
            )
            or 0
        )
        completed = (
            await session.scalar(
                select(func.count())
                .select_from(LessonProgress)
                .where(
                    LessonProgress.user_id == user.id,
                    LessonProgress.status == ProgressStatus.COMPLETED.value,
                    LessonProgress.lesson_id.in_(lesson_ids),
                )
            )
            or 0
        )

        result.append(
            AccountCourseOut(
                access=CourseAccessOut(
                    id=access.id,
                    source=access.source,
                    starts_at=access.starts_at,
                    expires_at=access.expires_at,
                    mentorship_ends_at=access.mentorship_ends_at,
                    offer=_offer_out(access.offer) if access.offer else None,
                ),
                course=course_summary_out(access.course),
                completed_lessons=completed,
                total_lessons=total,
            )
        )

    return result


async def update_progress(
    session: AsyncSession,
    user: User,
    course_slug: str,
    lesson_slug: str,
    payload: ProgressUpdateIn,
) -> ProgressOut:
    lesson = await get_published_lesson(session, course_slug, lesson_slug)
    if lesson is None:
        raise LookupError("Урок не найден")

    access = await get_active_access(session, user.id, lesson.module.course_id)
    if access is None:
        raise PermissionError("Нет доступа к уроку")

    progress = await session.scalar(
        select(LessonProgress).where(
            LessonProgress.user_id == user.id,
            LessonProgress.lesson_id == lesson.id,
        )
    )
    if progress is None:
        progress = LessonProgress(user_id=user.id, lesson_id=lesson.id)
        session.add(progress)

    progress.status = payload.status
    progress.last_position_seconds = payload.last_position_seconds
    progress.completed_at = (
        datetime.now(UTC)
        if payload.status == ProgressStatus.COMPLETED.value
        else None
    )

    await session.commit()
    await session.refresh(progress)
    return _progress_out(progress)  # type: ignore[return-value]
