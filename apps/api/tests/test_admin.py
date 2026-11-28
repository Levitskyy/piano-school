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


async def test_admin_manages_lesson_packages(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    payload = {
        "name": "Ученик",
        "email": "student@example.com",
        "password": "student-secret-123",
        "timezone": "Europe/Moscow",
    }
    assert (await client.post("/auth/register", json=payload)).status_code == 201
    assert (await client.post("/auth/login", json={
        "email": payload["email"],
        "password": payload["password"],
    })).status_code == 200
    assert (await client.post("/admin/products", json={
        "title": "Чужой пакет", "lessons_count": 2, "price": "1000",
    })).status_code == 403
    assert (await client.delete("/admin/products/single")).status_code == 403
    client.cookies.clear()

    await login_as_admin(client, session_factory)

    created = await client.post(
        "/admin/products",
        json={
            "title": "Пакет из 6 уроков",
            "description": "Шесть занятий с обратной связью",
            "lessons_count": 6,
            "price": "7490",
            "validity_days": 180,
        },
    )
    assert created.status_code == 201, created.text
    offer = created.json()
    assert offer["slug"] == "paket-iz-6-urokov"
    assert offer["kind"] == "package"
    assert offer["price_minor"] == 749_000
    assert offer["validity_days"] == 180
    assert offer["is_active"] is True

    public = await client.get("/individual-lessons/offers")
    public_offer = next(item for item in public.json() if item["slug"] == offer["slug"])
    assert public_offer["validity_days"] == 180

    updated = await client.patch(
        f"/admin/products/{offer['slug']}",
        json={
            "title": "Пакет из 5 уроков",
            "description": "Обновлённое описание",
            "lessons_count": 5,
            "price": "6999.99",
            "validity_days": 200,
            "is_active": False,
        },
    )
    assert updated.status_code == 200, updated.text
    changed = updated.json()
    assert changed["title"] == "Пакет из 5 уроков"
    assert changed["description"] == "Обновлённое описание"
    assert changed["lessons_count"] == 5
    assert changed["price_minor"] == 699_999
    assert changed["validity_days"] == 200
    assert changed["is_active"] is False

    public = await client.get("/individual-lessons/offers")
    assert all(item["slug"] != offer["slug"] for item in public.json())

    enabled = await client.patch(
        f"/admin/products/{offer['slug']}", json={"is_active": True}
    )
    assert enabled.status_code == 200
    assert enabled.json()["is_active"] is True
    # Поле не передано — срок действия должен остаться прежним.
    assert enabled.json()["validity_days"] == 200

    cleared = await client.patch(
        f"/admin/products/{offer['slug']}", json={"validity_days": None}
    )
    assert cleared.status_code == 200
    assert cleared.json()["validity_days"] is None

    duplicate = await client.post(
        "/admin/products",
        json={
            "title": "Дубль",
            "slug": "paket-iz-6-urokov",
            "lessons_count": 2,
            "price": "1000",
        },
    )
    assert duplicate.status_code == 409

    invalid = await client.post(
        "/admin/products",
        json={"title": "Некорректный", "lessons_count": 0, "price": "1000"},
    )
    assert invalid.status_code == 422

    promo = await client.post(
        "/admin/promo-codes", json={"percent": "10", "offer_slug": offer["slug"]}
    )
    assert promo.status_code == 201, promo.text
    blocked = await client.delete(f"/admin/products/{offer['slug']}")
    assert blocked.status_code == 409
    assert "Скройте" in blocked.json()["detail"]

    disposable = await client.post(
        "/admin/products",
        json={"title": "Пробный пакет", "lessons_count": 3, "price": "2000"},
    )
    assert disposable.status_code == 201
    deleted = await client.delete(f"/admin/products/{disposable.json()['slug']}")
    assert deleted.status_code == 204
    remaining = await client.get("/admin/products")
    assert all(item["slug"] != disposable.json()["slug"] for item in remaining.json())


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
        json={"percent": "33.33", "offer_slug": "single", "code": "admin33"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["code"] == "ADMIN33"
    assert Decimal(created.json()["discount_percent"]) == Decimal("33.33")
    assert created.json()["offer_id"] == single["id"]

    duplicate = await client.post(
        "/admin/promo-codes",
        json={"percent": "10", "offer_slug": "single", "code": "ADMIN33"},
    )
    assert duplicate.status_code == 409

    generated = await client.post(
        "/admin/promo-codes",
        json={"percent": "15", "offer_slug": "package-4"},
    )
    assert generated.status_code == 201, generated.text
    assert len(generated.json()["code"]) == 8

    unknown_offer = await client.post(
        "/admin/promo-codes",
        json={"percent": "10", "offer_slug": "missing"},
    )
    assert unknown_offer.status_code == 404

    listed = await client.get("/admin/promo-codes")
    assert listed.status_code == 200
    codes = {item["code"] for item in listed.json()}
    assert {"ADMIN33", generated.json()["code"]} <= codes

    bad_percent = await client.post(
        "/admin/promo-codes",
        json={"percent": "0", "offer_slug": "single", "code": "BAD"},
    )
    assert bad_percent.status_code == 422
