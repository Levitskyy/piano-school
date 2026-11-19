import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import get_settings
from app.core.rate_limit import enforce_rate_limit
from app.db import get_session
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordIn,
    ForgotPasswordOut,
    LoginIn,
    MessageOut,
    RegisterIn,
    ResetPasswordIn,
    UserOut,
)
from app.services import auth as auth_service
from app.services.email import (
    EmailNotConfiguredError,
    get_email_sender,
    send_password_reset_email,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_ttl_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        secure=settings.cookie_secure,
        samesite="lax",
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterIn,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> User:
    await enforce_rate_limit(
        scope="register",
        identity=payload.email,
        limit=10,
        window_seconds=60 * 60,
    )
    try:
        user = await auth_service.create_user(
            session,
            name=payload.name,
            email=payload.email,
            password=payload.password,
            timezone_name=payload.timezone,
            preferred_language=payload.preferred_language,
        )
    except auth_service.EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует",
        ) from exc

    token = await auth_service.create_session(
        session,
        user=user,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    _set_session_cookie(response, token)
    return user


@router.post("/login", response_model=UserOut)
async def login(
    payload: LoginIn,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> User:
    await enforce_rate_limit(
        scope="login",
        identity=payload.email,
        limit=20,
        window_seconds=15 * 60,
    )
    user = await auth_service.authenticate(
        session, email=payload.email, password=payload.password
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )

    token = await auth_service.create_session(
        session,
        user=user,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    _set_session_cookie(response, token)
    return user


@router.post("/logout", response_model=MessageOut)
async def logout(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> MessageOut:
    token = request.cookies.get(get_settings().session_cookie_name)
    if token:
        await auth_service.revoke_session(session, token)
    _clear_session_cookie(response)
    return MessageOut(message="Вы вышли из аккаунта")


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def forgot_password(
    payload: ForgotPasswordIn,
    session: AsyncSession = Depends(get_session),
) -> ForgotPasswordOut:
    settings = get_settings()
    await enforce_rate_limit(
        scope="forgot-password",
        identity=payload.email,
        limit=5,
        window_seconds=60 * 60,
    )

    try:
        sender = get_email_sender(settings)
    except EmailNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Восстановление пароля временно недоступно",
        ) from exc

    user = await auth_service.get_user_by_email(session, payload.email)
    dev_reset_url = None

    if user is not None:
        token = await auth_service.create_password_reset(session, user)
        reset_url = f"{settings.frontend_url}/reset-password?token={token}"
        try:
            await send_password_reset_email(
                sender,
                to=user.email,
                name=user.name,
                reset_url=reset_url,
                ttl_minutes=settings.password_reset_ttl_minutes,
            )
        except Exception as exc:
            logger.exception("Не удалось отправить письмо восстановления пароля")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Не удалось отправить письмо. Попробуйте позже",
            ) from exc

        if settings.is_local:
            dev_reset_url = reset_url

    return ForgotPasswordOut(
        message="Если аккаунт существует, мы отправили ссылку для восстановления.",
        dev_reset_url=dev_reset_url,
    )


@router.post("/reset-password", response_model=MessageOut)
async def reset_password(
    payload: ResetPasswordIn,
    session: AsyncSession = Depends(get_session),
) -> MessageOut:
    updated = await auth_service.reset_password(
        session, token=payload.token, new_password=payload.new_password
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ссылка недействительна или истекла",
        )
    return MessageOut(message="Пароль обновлён. Войдите с новым паролем.")
