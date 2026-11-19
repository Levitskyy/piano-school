from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.db import get_session
from app.models.user import User, UserRole
from app.schemas.teacher import TeacherLessonBookingOut, TeacherLessonUpdateIn
from app.services import teacher as teacher_service

router = APIRouter(prefix="/teacher", tags=["teacher"])

TEACHER_ROLES = (UserRole.TEACHER, UserRole.ADMIN)


@router.get("/lessons", response_model=list[TeacherLessonBookingOut])
async def list_lessons(
    _: User = Depends(require_roles(*TEACHER_ROLES)),
    session: AsyncSession = Depends(get_session),
) -> list[TeacherLessonBookingOut]:
    return await teacher_service.list_bookings(session)


@router.patch("/lessons/{booking_id}", response_model=TeacherLessonBookingOut)
async def update_lesson(
    booking_id: UUID,
    payload: TeacherLessonUpdateIn,
    _: User = Depends(require_roles(*TEACHER_ROLES)),
    session: AsyncSession = Depends(get_session),
) -> TeacherLessonBookingOut:
    try:
        return await teacher_service.update_meeting_url(
            session, booking_id, payload.meeting_url
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
