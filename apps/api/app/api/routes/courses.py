from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db import get_session
from app.models.user import User
from app.schemas.course import (
    CourseOut,
    CourseSummaryOut,
    LessonDetailOut,
    ProgressOut,
    ProgressUpdateIn,
)
from app.services import courses as course_service

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[CourseSummaryOut])
async def list_courses(
    session: AsyncSession = Depends(get_session),
) -> list[CourseSummaryOut]:
    courses = await course_service.list_published_courses(session)
    return [course_service.course_summary_out(course) for course in courses]


@router.get("/{slug}", response_model=CourseOut)
async def get_course(
    slug: str,
    session: AsyncSession = Depends(get_session),
) -> CourseOut:
    course = await course_service.get_published_course(session, slug)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Курс не найден")
    return course_service.course_out(course)


@router.get("/{slug}/lessons/{lesson_slug}", response_model=LessonDetailOut)
async def get_lesson(
    slug: str,
    lesson_slug: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> LessonDetailOut:
    try:
        lesson = await course_service.get_lesson_detail(
            session, user, slug, lesson_slug
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к уроку",
        ) from exc

    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Урок не найден")
    return lesson


@router.patch("/{slug}/lessons/{lesson_slug}/progress", response_model=ProgressOut)
async def update_lesson_progress(
    slug: str,
    lesson_slug: str,
    payload: ProgressUpdateIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ProgressOut:
    try:
        return await course_service.update_progress(
            session, user, slug, lesson_slug, payload
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Урок не найден"
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к уроку",
        ) from exc
