# Онлайн-школа фортепиано

Проект онлайн-школы фортепиано: продажа видеокурсов, разовых уроков и пакетов занятий с автоматической выдачей доступа после оплаты.

Классическая школа. Живая музыка.

- Исходный бриф: [docs/piano-school-project.md](docs/piano-school-project.md)
- Функциональное ТЗ: [docs/online-piano-school-agent-spec.md](docs/online-piano-school-agent-spec.md)
- Зафиксированные решения: [docs/project-foundation.md](docs/project-foundation.md)
- План реализации: [docs/implementation-plan.md](docs/implementation-plan.md)
- Процесс разработки и деплоя: [docs/development-workflow.md](docs/development-workflow.md)

## Стек

- **Web:** Next.js 16 (App Router), React 19, TypeScript
- **API:** FastAPI, Pydantic v2, SQLAlchemy 2 (async), Alembic
- **Данные:** PostgreSQL 17, Redis 8 (ARQ для фоновых задач)
- **Инфраструктура:** Docker Compose, GitHub Actions
- **Пакеты:** pnpm (JS), uv (Python)

## Структура

```
apps/web        Next.js: публичные страницы и личный кабинет
apps/api        FastAPI: бизнес-логика, БД, платежи, фоновый воркер
packages/       общие пакеты (типизированный API-клиент — позже)
infra/          docker-compose для локального/staging окружения
docs/           бриф и зафиксированные решения
```

## Быстрый старт

Нужны: Node.js 22+, pnpm 9+, Python 3.12+, [uv](https://docs.astral.sh/uv/). Docker — по желанию, для PostgreSQL и Redis.

```bash
cp .env.example .env
# В .env замените SECRET_KEY: openssl rand -hex 32
make install        # pnpm install + uv sync
make db-up          # PostgreSQL и Redis в Docker (или поднимите локально)
make migrate        # миграции Alembic
make dev-stack      # БД + API + web в фоне
```

- Сайт: http://localhost:3000
- API и OpenAPI: http://127.0.0.1:8000/docs
- Логи фонового запуска: `/tmp/piano-school/api.log`, `/tmp/piano-school/web.log`

Локальный PostgreSQL в Docker слушает порт `55432`, чтобы не конфликтовать с системным PostgreSQL или SSH-туннелем на `5432`. Без Docker поднимите PostgreSQL и Redis локально и поправьте `DATABASE_URL` / `REDIS_URL` в `.env`.

Браузер не обращается к FastAPI напрямую: Next.js проксирует `/api/*` в API. Поэтому cookie сессии выдаётся на домене сайта, а API можно держать только на `127.0.0.1`.

### Авторизация

- `/register` — регистрация ученика;
- `/login` — вход;
- `/forgot-password` — запрос ссылки восстановления;
- `/reset-password?token=...` — новый пароль;
- `/verify-email?token=...` — подтверждение email после регистрации (без токена — инструкция и повторная отправка);
- `/courses` — каталог курса;
- `/courses/[slug]` — курс, программа и варианты покупки;
- `/courses/[slug]/lessons/[lessonSlug]` — урок (нужен доступ);
- `/account` и `/account/courses` — кабинет ученика;
- `/teacher-panel` — панель преподавателя;
- `/admin` — панель администратора;
- `/payment/success?order_id=...` (или `?order_num=...` после Prodamus) — результат оплаты: статус берётся из API, а не из адреса страницы.

Запуск только с индивидуальными занятиями: `COURSES_ENABLED=false` в `.env` убирает
каталог, страницы и API курсов (404), а также ссылки на них из меню. Отдельная ветка
для этого не нужна.

Оплата уроков идёт через ЮKassa или Prodamus (RUB). На проде ЮKassa подключена и проверена
тестовым платежом 25.11.2026; ключи Prodamus на сервере пока не заданы. Prodamus
предназначен для иностранных карт, включая карты из США; конвертацию делает банк покупателя.
Цены тарифов задаются в админке или CLI:

```bash
make set-price slug=single price=1500
make promo-code percent=33.33 offer=single   # 1500 ₽ → 1000 ₽, только разовый урок
```

Промокод вводится на странице `/individual-lessons` перед переходом к оплате и действует
только на тариф, выбранный при создании (`single`, `package-4`, `package-8`).
Оба сервиса получают уже итоговую сумму; чеки для самозанятого настраиваются в кабинете
выбранного сервиса. На проде сейчас заданы цены 1500 / 5899 / 11499 ₽ — их нужно
подтвердить как финальные до приёма реальных платежей.

- ЮKassa: `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY`, `YOOKASSA_RETURN_URL`; webhook
  `https://levickaya.ru/api/payments/yookassa/webhook`. HTTP-уведомления не подписаны —
  сервер проверяет IP и уточняет статус платежа через API. На проде ключи заполнены и
  тестовый платёж прошёл 25.11.2026: заказ `succeeded`, занятие и пакет созданы.
- Prodamus: `PRODAMUS_FORM_URL`, `PRODAMUS_SECRET_KEY`, `PRODAMUS_PAYMENT_METHOD=monetaworld`,
  `PRODAMUS_CURRENCY=rub`, `PRODAMUS_SUCCESS_URL=https://levickaya.ru`; webhook
  `https://levickaya.ru/api/payments/prodamus/webhook`. Подпись в заголовке `Sign`
  обязательна; страница результата доступ не выдаёт. Тестовый платёж 26.11.2026 прошёл.

В админке `/admin/products` (роль `admin`) можно добавлять, редактировать и удалять тарифы:
название, описание, число уроков, цену, срок действия в днях и видимость на сайте. Тариф,
по которому уже есть
заказы, пакеты или промокоды, удалить нельзя — его можно только скрыть, чтобы сохранить
историю. Ключ тарифа создаётся из названия либо задаётся вручную; он нужен для CLI и
промокодов. Промокоды управляются на `/admin/promo-codes`. CLI из таблицы ниже остаётся
для автоматизации.

Email-провайдер на проде — Resend (`EMAIL_PROVIDER=resend`, `RESEND_API_KEY`, `EMAIL_FROM`); поддерживается также Unisender Go. В `local` ссылки восстановления и подтверждения возвращаются в ответе API и дублируются в консоль. В production без настроенного провайдера запросы на отправку письма вернут 503.

После регистрации сессия создаётся сразу, но оплата и запись на урок доступны только после подтверждения email. Ссылка действует 24 часа; повторную отправку можно запросить на `/verify-email`. Существующие аккаунты миграцией считаются подтверждёнными.

Роли назначаются вручную:

```bash
make role email=teacher@example.com role=teacher
make role email=admin@example.com role=admin
```

### Доступ из домашней сети (Windows + WSL)

По умолчанию dev-сервер доступен только на localhost. Чтобы открыть сайт с телефона или планшета:

```bash
make dev-stack     # БД, API на 127.0.0.1:8000 и Next.js на 0.0.0.0:3000
make lan           # в другом терминале: проброс Windows 8080 -> WSL 3000
```

`make lan` запросит права администратора (UAC) и создаст правило firewall. Откройте на устройстве в той же Wi-Fi сети адрес, который выведет команда, например `http://192.168.1.151:8080`. API наружу не публикуется: запросы идут через Next.js.

После перезапуска WSL IP меняется — просто выполните `make lan` снова. Не пробрасывайте порт на роутере: это dev-сервер, не предназначенный для интернета.

Полный стек в контейнерах:

```bash
docker compose -f infra/docker-compose.yml up --build
```

## Команды

| Команда | Что делает |
|---|---|
| `make install` | Установить зависимости |
| `make dev-stack` | Поднять БД, API и web в фоне |
| `make dev-api` / `make dev-web` | Запустить API / фронтенд |
| `make dev-web-lan` | Запустить фронтенд для доступа из домашней сети |
| `make lan` | Пробросить порт Windows → WSL (один раз, нужен UAC) |
| `make migrate` | Применить миграции |
| `make revision m="..."` | Создать миграцию по моделям |
| `make role email=... role=...` | Назначить роль пользователю |
| `make seed-demo` | Создать демонстрационный курс |
| `make seed-lessons` | Создать тарифы индивидуальных занятий (1/4/8 уроков) |
| `make seed-slots days=30` | Создать свободные слоты расписания |
| `make set-price slug=single price=1500` | Задать цену тарифа в рублях |
| `make promo-code percent=33.33 offer=single [code=...]` | Создать одноразовый процентный промокод на тариф |
| `make grant-access email=... course=... offer=...` | Вручную выдать доступ к курсу |
| `make lint` | Ruff + ESLint |
| `make test` | pytest |
| `make check` | lint + test + typecheck |

## Правила

- Фундамент меняется только через `docs/project-foundation.md`.
- Пункты брифа с пометкой **(предложение)** не считаются утверждёнными, пока не попали в документ фундамента.
- Оплата, доступ к контенту и данные детей — зоны повышенной осторожности: уточняйте неопределённости, не выдумывайте юридические требования.
