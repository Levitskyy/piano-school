from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import (
    generate_token,
    hash_password,
    hash_token,
    needs_rehash,
    verify_password,
)
from app.models.session import (
    EmailVerificationToken,
    PasswordResetToken,
    UserSession,
)
from app.models.user import StudentProfile, User, UserRole


class EmailAlreadyExistsError(Exception):
    """Email уже занят другим аккаунтом."""


def normalize_email(email: str) -> str:
    return email.strip().lower()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    return await session.scalar(select(User).where(User.email == normalize_email(email)))


async def create_user(
    session: AsyncSession,
    *,
    name: str,
    email: str,
    password: str,
    timezone_name: str = "Europe/Moscow",
    preferred_language: str = "ru",
) -> User:
    normalized_email = normalize_email(email)
    existing = await get_user_by_email(session, normalized_email)
    if existing is not None:
        raise EmailAlreadyExistsError

    user = User(
        name=name.strip(),
        email=normalized_email,
        password_hash=hash_password(password),
        role=UserRole.STUDENT.value,
        timezone=timezone_name,
        preferred_language=preferred_language,
    )
    user.student_profile = StudentProfile()
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise EmailAlreadyExistsError from exc
    await session.refresh(user)
    return user


async def authenticate(session: AsyncSession, *, email: str, password: str) -> User | None:
    user = await get_user_by_email(session, email)
    if user is None or not verify_password(password, user.password_hash):
        return None

    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
        await session.commit()

    return user


async def create_session(
    session: AsyncSession,
    *,
    user: User,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> str:
    settings = get_settings()
    token = generate_token()
    session.add(
        UserSession(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.session_ttl_days),
            user_agent=(user_agent or "")[:500] or None,
            ip_address=ip_address,
        )
    )
    await session.commit()
    return token


async def get_user_for_session(session: AsyncSession, token: str) -> User | None:
    token_hash = hash_token(token)
    user = await session.scalar(
        select(User)
        .join(UserSession, UserSession.user_id == User.id)
        .where(
            UserSession.token_hash == token_hash,
            UserSession.expires_at > datetime.now(UTC),
        )
    )
    return user


async def revoke_session(session: AsyncSession, token: str) -> None:
    await session.execute(
        delete(UserSession).where(UserSession.token_hash == hash_token(token))
    )
    await session.commit()


async def revoke_all_sessions(session: AsyncSession, user_id: UUID) -> None:
    await session.execute(delete(UserSession).where(UserSession.user_id == user_id))
    await session.commit()


async def create_password_reset(session: AsyncSession, user: User) -> str:
    settings = get_settings()
    token = generate_token()
    session.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=datetime.now(UTC)
            + timedelta(minutes=settings.password_reset_ttl_minutes),
        )
    )
    await session.commit()
    return token


async def create_email_verification(session: AsyncSession, user: User) -> str:
    """Создаёт новую ссылку подтверждения, делая предыдущие недействительными."""
    settings = get_settings()
    await session.execute(
        delete(EmailVerificationToken).where(EmailVerificationToken.user_id == user.id)
    )
    token = generate_token()
    session.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=datetime.now(UTC)
            + timedelta(minutes=settings.email_verification_ttl_minutes),
        )
    )
    await session.commit()
    return token


async def verify_email(session: AsyncSession, *, token: str) -> bool:
    verification = await session.scalar(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == hash_token(token),
            EmailVerificationToken.expires_at > datetime.now(UTC),
        )
    )
    if verification is None:
        return False

    user = await session.get(User, verification.user_id)
    if user is None:
        return False

    user.email_verified_at = datetime.now(UTC)
    await session.execute(
        delete(EmailVerificationToken).where(
            EmailVerificationToken.user_id == user.id
        )
    )
    await session.commit()
    return True


async def reset_password(session: AsyncSession, *, token: str, new_password: str) -> bool:
    reset = await session.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == hash_token(token),
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > datetime.now(UTC),
        )
    )
    if reset is None:
        return False

    user = await session.get(User, reset.user_id)
    if user is None:
        return False

    now = datetime.now(UTC)
    user.password_hash = hash_password(new_password)
    reset.used_at = now
    await session.execute(delete(UserSession).where(UserSession.user_id == user.id))
    await session.commit()
    return True
