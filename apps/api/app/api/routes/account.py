from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import get_settings
from app.db import get_session
from app.models.user import User
from app.schemas.auth import ProfileUpdateIn, UserOut
from app.schemas.course import AccountCourseOut
from app.services import courses as course_service

router = APIRouter(prefix="/account", tags=["account"])


def require_courses_enabled() -> None:
    if not get_settings().courses_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не найдено")


@router.get(
    "/courses",
    response_model=list[AccountCourseOut],
    dependencies=[Depends(require_courses_enabled)],
)
async def list_courses(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[AccountCourseOut]:
    return await course_service.list_account_courses(session, user)


@router.patch("/profile", response_model=UserOut)
async def update_profile(
    payload: ProfileUpdateIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> User:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(user, field, value)

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
