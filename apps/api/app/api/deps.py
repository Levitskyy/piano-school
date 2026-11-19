from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session
from app.models.user import User, UserRole
from app.services.auth import get_user_for_session

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Требуется вход",
    headers={"WWW-Authenticate": "Cookie"},
)


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> User:
    token = request.cookies.get(get_settings().session_cookie_name)
    if not token:
        raise CREDENTIALS_EXCEPTION

    user = await get_user_for_session(session, token)
    if user is None:
        raise CREDENTIALS_EXCEPTION

    return user


async def get_optional_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> User | None:
    token = request.cookies.get(get_settings().session_cookie_name)
    if not token:
        return None
    return await get_user_for_session(session, token)


def require_roles(*roles: UserRole) -> Callable:
    allowed = {role.value for role in roles}

    async def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав",
            )
        return user

    return dependency
