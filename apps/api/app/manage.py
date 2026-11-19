"""Небольшие административные команды для локальной эксплуатации."""

import argparse
import asyncio
from datetime import UTC, datetime, timedelta

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
from app.models.user import User, UserRole
from app.services.auth import normalize_email

DEMO_COURSE_SLUG = "fortepiano"


async def set_role(email: str, role: str) -> None:
    if role not in {item.value for item in UserRole}:
        raise SystemExit(f"Неизвестная роль: {role}")

    async with SessionLocal() as session:
        user = await session.scalar(
            select(User).where(User.email == normalize_email(email))
        )
        if user is None:
            raise SystemExit(f"Пользователь не найден: {email}")

        user.role = role
        await session.commit()
        print(f"{user.email}: роль {user.role}")


async def grant_access(email: str, course_slug: str, offer_slug: str) -> None:
    async with SessionLocal() as session:
        user = await session.scalar(
            select(User).where(User.email == normalize_email(email))
        )
        if user is None:
            raise SystemExit(f"Пользователь не найден: {email}")

        course = await session.scalar(
            select(Course).where(Course.slug == course_slug)
        )
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
                now + timedelta(days=offer.mentorship_days)
                if offer.mentorship_days
                else None
            ),
        )
        session.add(access)
        await session.commit()
        print(f"{user.email}: доступ к {course.slug} ({offer.slug}) выдан")


async def seed_demo_course() -> None:
    async with SessionLocal() as session:
        existing = await session.scalar(
            select(Course).where(Course.slug == DEMO_COURSE_SLUG)
        )
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Piano School management commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    role_parser = subparsers.add_parser("set-role", help="Изменить роль пользователя")
    role_parser.add_argument("--email", required=True)
    role_parser.add_argument("--role", required=True, choices=[r.value for r in UserRole])

    access_parser = subparsers.add_parser(
        "grant-access", help="Выдать доступ к курсу вручную"
    )
    access_parser.add_argument("--email", required=True)
    access_parser.add_argument("--course", required=True)
    access_parser.add_argument("--offer", required=True)

    subparsers.add_parser("seed-demo-course", help="Создать демонстрационный курс")

    args = parser.parse_args()
    if args.command == "set-role":
        asyncio.run(set_role(args.email, args.role))
    elif args.command == "grant-access":
        asyncio.run(grant_access(args.email, args.course, args.offer))
    elif args.command == "seed-demo-course":
        asyncio.run(seed_demo_course())


if __name__ == "__main__":
    main()
