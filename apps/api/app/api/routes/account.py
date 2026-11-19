from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db import get_session
from app.models.user import User
from app.schemas.auth import ProfileUpdateIn, UserOut
from app.schemas.course import AccountCourseOut
from app.services import courses as course_service

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/courses", response_model=list[AccountCourseOut])
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
