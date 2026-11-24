"""Небольшие административные команды для локальной эксплуатации."""

import argparse
import asyncio
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.db import SessionLocal
from app.models.course import (
    Course,
    CourseAccess,
    CourseModule,
    CourseOffer,
    CourseStatus,
    Lesson,
    LessonStatus,
    OfferKind,
    VideoStatus,
)
from app.models.individual_lessons import (
    IndividualLessonOffer,
    IndividualLessonOfferKind,
    LessonSlot,
    LessonSlotStatus,
)
from app.models.user import User, UserRole
from app.services import admin as admin_service
from app.services.auth import normalize_email

DEMO_COURSE_SLUG = "fortepiano"


async def set_role(email: str, role: str) -> None:
    if role not in {item.value for item in UserRole}:
        raise SystemExit(f"Неизвестная роль: {role}")

    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.email == normalize_email(email)))
        if user is None:
            raise SystemExit(f"Пользователь не найден: {email}")

        user.role = role
        await session.commit()
        print(f"{user.email}: роль {user.role}")


async def grant_access(email: str, course_slug: str, offer_slug: str) -> None:
    async with SessionLocal() as session:
        user = await session.scalar(select(User).where(User.email == normalize_email(email)))
        if user is None:
            raise SystemExit(f"Пользователь не найден: {email}")

        course = await session.scalar(select(Course).where(Course.slug == course_slug))
        if course is None:
            raise SystemExit(f"Курс не найден: {course_slug}")

        offer = await session.scalar(
            select(CourseOffer).where(
                CourseOffer.course_id == course.id,
                CourseOffer.slug == offer_slug,
            )
        )
        if offer is None:
            raise SystemExit(f"Вариант покупки не найден: {offer_slug}")

        now = datetime.now(UTC)
        access = CourseAccess(
            user_id=user.id,
            course_id=course.id,
            offer_id=offer.id,
            source="manual",
            starts_at=now,
            mentorship_ends_at=(
                now + timedelta(days=offer.mentorship_days) if offer.mentorship_days else None
            ),
        )
        session.add(access)
        await session.commit()
        print(f"{user.email}: доступ к {course.slug} ({offer.slug}) выдан")


async def seed_demo_course() -> None:
    async with SessionLocal() as session:
        existing = await session.scalar(select(Course).where(Course.slug == DEMO_COURSE_SLUG))
        if existing is not None:
            print(f"Курс уже существует: {existing.slug}")
            return

        course = Course(
            slug=DEMO_COURSE_SLUG,
            title="Фортепиано: первый семестр",
            subtitle="Демонстрационная программа курса",
            description=(
                "Спокойный путь от посадки и первого звука к самостоятельной игре. "
                "Это демонстрационное наполнение: замените тексты, уроки и цены "
                "перед запуском."
            ),
            level="beginner",
            status=CourseStatus.PUBLISHED.value,
            position=0,
        )

        modules = [
            (
                "Посадка и звук",
                "Как сидеть за инструментом, ставить руку и извлекать ровный звук.",
                "posadka-i-zvuk",
            ),
            (
                "Нотная грамота",
                "Ритм, интервалы и простые тональности на понятных примерах.",
                "notnaya-gramota",
            ),
            (
                "Первые произведения",
                "Собираем пьесу по фрагментам: аппликатура, фразировка и педаль.",
                "pervye-proizvedeniya",
            ),
            (
                "Самостоятельная игра",
                "Как разбирать новое произведение и заниматься без преподавателя.",
                "samostoyatelnaya-igra",
            ),
            (
                "Работа с педалью",
                "Педаль как часть звука, а не механическое действие.",
                "rabota-s-pedalyu",
            ),
            (
                "Итоговая пьеса",
                "Собираем целую пьесу и готовим её к исполнению.",
                "itogovaya-pesa",
            ),
        ]

        for position, (title, description, lesson_slug) in enumerate(modules, start=1):
            module = CourseModule(
                title=title,
                description=description,
                position=position,
            )
            module.lessons.append(
                Lesson(
                    slug=lesson_slug,
                    title=f"Урок {position}. {title}",
                    description=description,
                    position=1,
                    duration_seconds=None,
                    status=LessonStatus.PUBLISHED.value,
                    video_status=VideoStatus.PENDING.value,
                )
            )
            course.modules.append(module)

        course.offers.extend(
            [
                CourseOffer(
                    slug="self-study",
                    title="Самостоятельное обучение",
                    description=(
                        "Доступ к урокам и материалам курса. Занимайтесь в своём темпе "
                        "и возвращайтесь к урокам, когда удобно."
                    ),
                    kind=OfferKind.SELF_STUDY.value,
                    position=0,
                ),
                CourseOffer(
                    slug="with-mentorship",
                    title="С сопровождением",
                    description=(
                        "Курс плюс период сопровождения: обратная связь по домашним "
                        "заданиям и разбор практики. Без автопродления."
                    ),
                    kind=OfferKind.WITH_MENTORSHIP.value,
                    mentorship_days=90,
                    position=1,
                ),
            ]
        )

        session.add(course)
        await session.commit()
        print(f"Создан демонстрационный курс: {course.slug}")


async def seed_individual_lesson_offers() -> None:
    offers = [
        IndividualLessonOffer(
            slug="single",
            title="Разовый урок",
            description=(
                "Одно индивидуальное занятие 60 минут. Удобный слот выбирается "
                "при покупке, ссылка на встречу добавляется преподавателем вручную."
            ),
            kind=IndividualLessonOfferKind.SINGLE.value,
            lessons_count=1,
            duration_minutes=60,
            position=0,
        ),
        IndividualLessonOffer(
            slug="package-4",
            title="Пакет из 4 уроков",
            description=(
                "Четыре индивидуальных занятия по 60 минут. Первый слот выбирается "
                "при покупке, остальные — из остатка пакета в кабинете."
            ),
            kind=IndividualLessonOfferKind.PACKAGE.value,
            lessons_count=4,
            duration_minutes=60,
            validity_days=180,
            position=1,
        ),
        IndividualLessonOffer(
            slug="package-8",
            title="Пакет из 8 уроков",
            description=(
                "Восемь индивидуальных занятий по 60 минут. Записывайтесь на слоты "
                "по мере использования пакета."
            ),
            kind=IndividualLessonOfferKind.PACKAGE.value,
            lessons_count=8,
            duration_minutes=60,
            validity_days=365,
            position=2,
        ),
    ]

    async with SessionLocal() as session:
        created = 0
        for candidate in offers:
            existing = await session.scalar(
                select(IndividualLessonOffer).where(IndividualLessonOffer.slug == candidate.slug)
            )
            if existing is None:
                session.add(candidate)
                created += 1
        await session.commit()
        print(f"Создано тарифов индивидуальных занятий: {created}")


async def seed_lesson_slots(days: int = 30) -> None:
    teacher_tz = ZoneInfo("Europe/Moscow")
    now = datetime.now(UTC)
    slots: list[LessonSlot] = []

    for day_offset in range(1, days + 1):
        date = (now + timedelta(days=day_offset)).astimezone(teacher_tz).date()
        if date.weekday() == 6:
            continue
        for hour in range(10, 19):
            start_local = datetime.combine(date, time(hour=hour), tzinfo=teacher_tz)
            start_utc = start_local.astimezone(UTC)
            if start_utc <= now:
                continue
            slots.append(
                LessonSlot(
                    starts_at=start_utc,
                    ends_at=start_utc + timedelta(minutes=60),
                    duration_minutes=60,
                    status=LessonSlotStatus.FREE.value,
                )
            )

    async with SessionLocal() as session:
        existing = set((await session.scalars(select(LessonSlot.starts_at))).all())
        new_slots = [slot for slot in slots if slot.starts_at not in existing]
        session.add_all(new_slots)
        await session.commit()
        print(f"Создано слотов: {len(new_slots)}")


async def create_promo_code(
    percent: str, offer_slug: str, code: str | None = None
) -> None:
    try:
        value = Decimal(percent)
    except InvalidOperation as exc:
        raise SystemExit(f"Некорректный процент: {percent}") from exc

    async with SessionLocal() as session:
        try:
            promo = await admin_service.create_promo_code(session, value, offer_slug, code)
        except (
            ValueError,
            admin_service.OfferNotFoundError,
            admin_service.PromoCodeExistsError,
        ) as exc:
            raise SystemExit(str(exc)) from exc
    print(f"Создан промокод {promo.code}: скидка {promo.discount_percent}% на {offer_slug}")


async def set_offer_price(slug: str, price: str) -> None:
    try:
        value = Decimal(price)
    except InvalidOperation as exc:
        raise SystemExit(f"Некорректная цена: {price}") from exc

    async with SessionLocal() as session:
        try:
            offer = await admin_service.set_offer_price(session, slug, value)
        except (ValueError, admin_service.OfferNotFoundError) as exc:
            raise SystemExit(str(exc)) from exc
    print(f"{slug}: цена {Decimal(offer.price_minor) / 100} ₽")


def main() -> None:
    parser = argparse.ArgumentParser(description="Levickaya Piano management commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    role_parser = subparsers.add_parser("set-role", help="Изменить роль пользователя")
    role_parser.add_argument("--email", required=True)
    role_parser.add_argument("--role", required=True, choices=[r.value for r in UserRole])

    access_parser = subparsers.add_parser("grant-access", help="Выдать доступ к курсу вручную")
    access_parser.add_argument("--email", required=True)
    access_parser.add_argument("--course", required=True)
    access_parser.add_argument("--offer", required=True)

    subparsers.add_parser("seed-demo-course", help="Создать демонстрационный курс")
    subparsers.add_parser("seed-individual-lessons", help="Создать тарифы индивидуальных занятий")
    slots_parser = subparsers.add_parser(
        "seed-lesson-slots", help="Создать свободные слоты расписания"
    )
    slots_parser.add_argument("--days", type=int, default=30)

    promo_parser = subparsers.add_parser("create-promo-code", help="Создать одноразовый промокод")
    promo_parser.add_argument("--percent", required=True, help="Процент скидки, например 33.33")
    promo_parser.add_argument(
        "--offer", required=True, help="Тариф: single, package-4 или package-8"
    )
    promo_parser.add_argument("--code", help="Своё название кода; без него будет сгенерировано")

    price_parser = subparsers.add_parser("set-offer-price", help="Задать цену тарифа в рублях")
    price_parser.add_argument("--slug", required=True)
    price_parser.add_argument("--price", required=True)

    args = parser.parse_args()
    if args.command == "set-role":
        asyncio.run(set_role(args.email, args.role))
    elif args.command == "grant-access":
        asyncio.run(grant_access(args.email, args.course, args.offer))
    elif args.command == "seed-demo-course":
        asyncio.run(seed_demo_course())
    elif args.command == "seed-individual-lessons":
        asyncio.run(seed_individual_lesson_offers())
    elif args.command == "seed-lesson-slots":
        asyncio.run(seed_lesson_slots(args.days))
    elif args.command == "create-promo-code":
        asyncio.run(create_promo_code(args.percent, args.offer, args.code))
    elif args.command == "set-offer-price":
        asyncio.run(set_offer_price(args.slug, args.price))


if __name__ == "__main__":
    main()
