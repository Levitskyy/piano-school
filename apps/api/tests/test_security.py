from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import ClassVar
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import Response
from httpx import AsyncClient
from redis.exceptions import RedisError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.routes import auth as auth_routes
from app.api.routes.auth import _set_session_cookie
from app.config import get_settings
from app.core import rate_limit
from app.core.security import hash_token
from app.models.individual_lessons import IndividualLessonOffer, LessonSlot
from app.models.payments import PurchaseOrder
from app.models.session import EmailVerificationToken
from app.models.user import User
from app.services.auth import create_session, get_user_by_email
from conftest import register_and_verify


class FakeRedis:
    """Один экземпляр на тест: лимит должен накапливаться между вызовами."""

    current: ClassVar[FakeRedis | None] = None

    def __init__(self, fail: bool = False) -> None:
        self.store: dict[str, int] = {}
        self.expiries: dict[str, int] = {}
        self.fail = fail
        self.closed = False
        FakeRedis.current = self

    @classmethod
    def from_url(cls, *_: object, **__: object) -> FakeRedis:
        return cls.current or cls()

    async def incr(self, key: str) -> int:
        if self.fail:
            raise RedisError("Redis недоступен")
        self.store[key] = self.store.get(key, 0) + 1
        return self.store[key]

    async def expire(self, key: str, seconds: int) -> None:
        self.expiries[key] = seconds

    async def aclose(self) -> None:
        self.closed = True


async def test_login_rate_limit_blocks_brute_force(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeRedis()
    # conftest отключает лимитер во всех тестах — здесь возвращаем настоящий.
    monkeypatch.setattr(auth_routes, "enforce_rate_limit", rate_limit.enforce_rate_limit)
    monkeypatch.setattr(rate_limit.Redis, "from_url", fake.from_url)
    payload = {"email": "brute@example.com", "password": "wrong-password"}

    for _ in range(20):
        assert (await client.post("/auth/login", json=payload)).status_code == 401

    blocked = await client.post("/auth/login", json=payload)
    assert blocked.status_code == 429
    assert blocked.headers["retry-after"] == "900"
    assert len(fake.expiries) == 1
    assert fake.closed


async def test_rate_limit_identity_is_normalized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeRedis()
    monkeypatch.setattr(rate_limit.Redis, "from_url", fake.from_url)

    for identity in (" Anna@Example.com ", "anna@example.com"):
        await rate_limit.enforce_rate_limit(
            scope="login", identity=identity, limit=5, window_seconds=900
        )

    assert list(fake.store) == [f"ratelimit:login:{hash_token('anna@example.com')}"]


async def test_rate_limit_fails_open_when_redis_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeRedis(fail=True)
    monkeypatch.setattr(rate_limit.Redis, "from_url", fake.from_url)

    await rate_limit.enforce_rate_limit(
        scope="login", identity="anna@example.com", limit=1, window_seconds=900
    )

    assert fake.closed


def test_session_cookie_is_hardened(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(
        "app.api.routes.auth.get_settings",
        lambda: SimpleNamespace(
            session_cookie_name=settings.session_cookie_name,
            session_ttl_days=settings.session_ttl_days,
            cookie_secure=True,
        ),
    )

    response = Response()
    _set_session_cookie(response, "opaque-token")
    cookie = response.headers["set-cookie"]

    assert "HttpOnly" in cookie
    assert "Secure" in cookie
    assert "samesite=lax" in cookie.lower()
    assert f"Max-Age={settings.session_ttl_days * 24 * 60 * 60}" in cookie


async def test_yookassa_webhook_trusts_only_last_forwarded_ip(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def pending_payment(*_: object, **__: object) -> dict[str, str]:
        return {"status": "pending"}

    monkeypatch.setattr("app.services.payments._yookassa", pending_payment)
    payload = {"type": "notification", "object": {"id": "pay-unknown"}}

    trusted = await client.post(
        "/payments/yookassa/webhook",
        json=payload,
        headers={"x-forwarded-for": "8.8.8.8, 185.71.76.1"},
    )
    assert trusted.status_code == 204

    spoofed = await client.post(
        "/payments/yookassa/webhook",
        json=payload,
        headers={"x-forwarded-for": "185.71.76.1, 8.8.8.8"},
    )
    assert spoofed.status_code == 403

    malformed = await client.post(
        "/payments/yookassa/webhook",
        json=payload,
        headers={"x-forwarded-for": "not-an-ip"},
    )
    assert malformed.status_code == 403


async def test_password_reset_is_single_use_and_revokes_sessions(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
) -> None:
    await client.post("/auth/register", json=register_payload)
    async with session_factory() as session:
        user = await get_user_by_email(session, register_payload["email"])
        assert user is not None
        other_session_token = await create_session(session, user=user)

    forgot = await client.post(
        "/auth/forgot-password", json={"email": register_payload["email"]}
    )
    assert forgot.status_code == 202
    token = parse_qs(urlparse(forgot.json()["dev_reset_url"]).query)["token"][0]
    reset_payload = {"token": token, "new_password": "new-secret-456"}

    assert (await client.post("/auth/reset-password", json=reset_payload)).status_code == 200
    assert (await client.post("/auth/reset-password", json=reset_payload)).status_code == 400
    assert (await client.get("/auth/me")).status_code == 401

    settings = get_settings()
    client.cookies.set(settings.session_cookie_name, other_session_token)
    assert (await client.get("/auth/me")).status_code == 401


async def test_expired_verification_token_is_rejected(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
) -> None:
    registered = await client.post("/auth/register", json=register_payload)
    token = parse_qs(
        urlparse(registered.json()["dev_verification_url"]).query
    )["token"][0]

    async with session_factory() as session:
        user = await get_user_by_email(session, register_payload["email"])
        assert user is not None
        await session.execute(
            update(EmailVerificationToken)
            .where(EmailVerificationToken.user_id == user.id)
            .values(expires_at=datetime.now(UTC) - timedelta(minutes=1))
        )
        await session.commit()

    response = await client.post("/auth/verify-email", json={"token": token})
    assert response.status_code == 400
    assert (await client.get("/auth/me")).json()["email_verified_at"] is None


async def test_payment_status_is_private_to_owner(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
) -> None:
    await register_and_verify(client, session_factory, register_payload)
    owner_cookies = dict(client.cookies)

    other_payload = {**register_payload, "email": "other@example.com"}
    await client.post("/auth/register", json=other_payload)
    other_cookies = dict(client.cookies)

    async with session_factory() as session:
        owner = await session.scalar(select(User).where(User.email == register_payload["email"]))
        assert owner is not None
        offer = IndividualLessonOffer(slug="single", title="Урок", price_minor=100_000)
        slot = LessonSlot(
            starts_at=datetime.now(UTC) + timedelta(days=1),
            ends_at=datetime.now(UTC) + timedelta(days=1, hours=1),
            duration_minutes=60,
        )
        session.add_all([offer, slot])
        await session.flush()
        order = PurchaseOrder(
            user_id=owner.id,
            offer_id=offer.id,
            slot_id=slot.id,
            price_minor=100_000,
            total_minor=100_000,
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
        )
        session.add(order)
        await session.commit()
        order_id = order.id

    client.cookies.clear()
    client.cookies.update(owner_cookies)
    owner_status = await client.get(f"/payments/{order_id}")
    assert owner_status.status_code == 200
    assert owner_status.json()["status"] == "pending"

    client.cookies.clear()
    client.cookies.update(other_cookies)
    other_status = await client.get(f"/payments/{order_id}")
    assert other_status.status_code == 404
