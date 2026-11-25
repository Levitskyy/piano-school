from urllib.parse import parse_qs, urlparse

from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.user import User


async def test_register_login_me_logout(
    client: AsyncClient, register_payload: dict[str, str]
) -> None:
    register = await client.post("/auth/register", json=register_payload)
    assert register.status_code == 201
    body = register.json()
    assert body["email"] == "anna@example.com"
    assert body["role"] == "student"
    assert client.cookies.get("ps_session")

    me = await client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["name"] == "Анна"

    logout = await client.post("/auth/logout")
    assert logout.status_code == 200
    assert client.cookies.get("ps_session") is None

    unauthorized = await client.get("/auth/me")
    assert unauthorized.status_code == 401

    login = await client.post(
        "/auth/login",
        json={"email": "ANNA@example.com", "password": "very-secret-123"},
    )
    assert login.status_code == 200
    assert login.json()["email"] == "anna@example.com"


async def test_duplicate_email_is_rejected(
    client: AsyncClient, register_payload: dict[str, str]
) -> None:
    first = await client.post("/auth/register", json=register_payload)
    assert first.status_code == 201

    second = await client.post(
        "/auth/register",
        json={**register_payload, "email": "ANNA@example.com"},
    )
    assert second.status_code == 409


async def test_invalid_login_is_rejected(
    client: AsyncClient, register_payload: dict[str, str]
) -> None:
    await client.post("/auth/register", json=register_payload)
    await client.post("/auth/logout")

    login = await client.post(
        "/auth/login",
        json={"email": register_payload["email"], "password": "wrong-password"},
    )
    assert login.status_code == 401


async def test_password_reset_flow(
    client: AsyncClient, register_payload: dict[str, str]
) -> None:
    await client.post("/auth/register", json=register_payload)
    await client.post("/auth/logout")

    forgot = await client.post(
        "/auth/forgot-password", json={"email": register_payload["email"]}
    )
    assert forgot.status_code == 202
    reset_url = forgot.json()["dev_reset_url"]
    assert reset_url

    token = parse_qs(urlparse(reset_url).query)["token"][0]
    reset = await client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "new-secret-456"},
    )
    assert reset.status_code == 200

    old_login = await client.post(
        "/auth/login",
        json={"email": register_payload["email"], "password": "very-secret-123"},
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/auth/login",
        json={"email": register_payload["email"], "password": "new-secret-456"},
    )
    assert new_login.status_code == 200


async def test_register_requires_email_verification_for_paid_actions(
    client: AsyncClient, register_payload: dict[str, str]
) -> None:
    registered = await client.post("/auth/register", json=register_payload)
    assert registered.status_code == 201
    body = registered.json()
    assert body["email_verified_at"] is None
    assert body["verification_email_sent"] is True
    assert body["dev_verification_url"]

    before = await client.get("/auth/me")
    assert before.json()["email_verified_at"] is None

    token = parse_qs(urlparse(body["dev_verification_url"]).query)["token"][0]
    verified = await client.post("/auth/verify-email", json={"token": token})
    assert verified.status_code == 200

    after = await client.get("/auth/me")
    assert after.json()["email_verified_at"] is not None

    reused = await client.post("/auth/verify-email", json={"token": token})
    assert reused.status_code == 400


async def test_resend_verification_replaces_previous_link(
    client: AsyncClient, register_payload: dict[str, str]
) -> None:
    registered = await client.post("/auth/register", json=register_payload)
    assert registered.status_code == 201
    old_token = parse_qs(urlparse(registered.json()["dev_verification_url"]).query)[
        "token"
    ][0]

    resent = await client.post("/auth/resend-verification")
    assert resent.status_code == 200
    assert resent.json()["verification_email_sent"] is True
    new_token = parse_qs(urlparse(resent.json()["dev_verification_url"]).query)[
        "token"
    ][0]
    assert new_token != old_token

    old_link = await client.post("/auth/verify-email", json={"token": old_token})
    assert old_link.status_code == 400

    new_link = await client.post("/auth/verify-email", json={"token": new_token})
    assert new_link.status_code == 200


async def test_profile_update(
    client: AsyncClient, register_payload: dict[str, str]
) -> None:
    await client.post("/auth/register", json=register_payload)

    update = await client.patch(
        "/account/profile",
        json={"name": "Анна Петрова", "timezone": "Asia/Tbilisi"},
    )
    assert update.status_code == 200
    assert update.json()["name"] == "Анна Петрова"
    assert update.json()["timezone"] == "Asia/Tbilisi"


async def test_profile_update_rejects_unknown_timezone(
    client: AsyncClient, register_payload: dict[str, str]
) -> None:
    await client.post("/auth/register", json=register_payload)

    response = await client.patch(
        "/account/profile",
        json={"timezone": "Москва, GMT+3"},
    )
    assert response.status_code == 422


async def test_admin_routes_require_admin(
    client: AsyncClient, register_payload: dict[str, str]
) -> None:
    await client.post("/auth/register", json=register_payload)

    response = await client.get("/admin/users")
    assert response.status_code == 403


async def test_admin_can_list_users(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    register_payload: dict[str, str],
) -> None:
    await client.post("/auth/register", json=register_payload)

    async with session_factory() as session:
        await session.execute(
            update(User)
            .where(User.email == register_payload["email"])
            .values(role="admin")
        )
        await session.commit()

    response = await client.get("/admin/users")
    assert response.status_code == 200
    assert response.json()[0]["email"] == register_payload["email"]
