from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.user import User, UserRole
from test_individual_lessons import seed_offers_and_slots


async def login_as_admin(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    payload = {
        "name": "Администратор",
        "email": "admin@example.com",
        "password": "admin-secret-123",
        "timezone": "Europe/Moscow",
    }
    assert (await client.post("/auth/register", json=payload)).status_code == 201
    async with session_factory() as session:
        admin = await session.scalar(select(User).where(User.email == payload["email"]))
        assert admin is not None
        admin.role = UserRole.ADMIN.value
        await session.commit()

    response = await client.post(
        "/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert response.status_code == 200


async def test_admin_prices_and_promo_codes(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await seed_offers_and_slots(session_factory)

    student = {
        "name": "Ученик",
        "email": "student@example.com",
        "password": "student-secret-123",
        "timezone": "Europe/Moscow",
    }
    assert (await client.post("/auth/register", json=student)).status_code == 201
    assert (await client.post("/auth/login", json={
        "email": student["email"],
        "password": student["password"],
    })).status_code == 200
    assert (await client.get("/admin/products")).status_code == 403
    client.cookies.clear()

    await login_as_admin(client, session_factory)

    products = await client.get("/admin/products")
    assert products.status_code == 200
    product_data = products.json()
    assert {item["slug"] for item in product_data} == {"single", "package-4"}
    single = next(item for item in product_data if item["slug"] == "single")
    assert single["price_minor"] == 150_000

    updated = await client.patch(
        "/admin/products/single/price",
        json={"price": "1700.50"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["price_minor"] == 170_050

    public = await client.get("/individual-lessons/offers")
    public_single = next(
        item for item in public.json() if item["slug"] == "single"
    )
    assert public_single["price_minor"] == 170_050

    bad_price = await client.patch(
        "/admin/products/single/price",
        json={"price": "0"},
    )
    assert bad_price.status_code == 422

    unknown = await client.patch(
        "/admin/products/unknown/price",
        json={"price": "1000"},
    )
    assert unknown.status_code == 404

    created = await client.post(
        "/admin/promo-codes",
        json={"percent": "33.33", "code": "admin33"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["code"] == "ADMIN33"
    assert Decimal(created.json()["discount_percent"]) == Decimal("33.33")

    duplicate = await client.post(
        "/admin/promo-codes",
        json={"percent": "10", "code": "ADMIN33"},
    )
    assert duplicate.status_code == 409

    generated = await client.post("/admin/promo-codes", json={"percent": "15"})
    assert generated.status_code == 201, generated.text
    assert len(generated.json()["code"]) == 8

    listed = await client.get("/admin/promo-codes")
    assert listed.status_code == 200
    codes = {item["code"] for item in listed.json()}
    assert {"ADMIN33", generated.json()["code"]} <= codes

    bad_percent = await client.post(
        "/admin/promo-codes",
        json={"percent": "0", "code": "BAD"},
    )
    assert bad_percent.status_code == 422
