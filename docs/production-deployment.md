# Продакшен на VPS (193.233.88.115)

Текущее состояние: домен `levickaya.ru` подключён, HTTPS работает (`curl -I https://levickaya.ru/` → 200, цепочка сертификата проверяется). `PUBLIC_BASE_URL=https://levickaya.ru`, письма отправляются через Resend.

## Что сделано на сервере

- Репозиторий склонирован в `/opt/piano-school`, работает ветка `master`.
- Установлены Docker Engine + plugin, nginx не ставится системно — используется контейнер nginx из compose.
- Открыты только порты **22 (SSH по ключу), 80, 443** (UFW).
- SSH: вход по паролю, keyboard-interactive, X11 и agent forwarding отключены; root по ключу разрешён; `MaxAuthTries=3`, `PerSourcePenalties=yes`.
- fail2ban: включены jails `nginx-req-limit` и `nginx-bad-host`. SSH-jail намеренно выключен из-за CVE-2026-109786 (в OpenSSH 26.04 встроены `PerSourcePenalties`, а уязвимый fail2ban-фильтр может банить чужой IP по подставленному имени пользователя).
- Включены автоматические security-обновления Ubuntu (без автоперезапуска).

## Структура на сервере

```
/opt/piano-school              # код (git)
/opt/piano-school/.env         # секреты; НЕ в git
/opt/piano-school/infra/production/
    docker-compose.yml
    nginx.conf
    snippets/{proxy.conf,tls-params.conf}
    selfsigned.{crt,key}
```

## Секреты и переменные

`/opt/piano-school/.env` содержит:

| Переменная | Значение |
|---|---|
| `ENVIRONMENT` | `production` (cookie `Secure=true`) |
| `SECRET_KEY` | случайный hex |
| `DATABASE_URL` | переопределяется в compose на контейнер postgres |
| `REDIS_URL` | переопределяется в compose |
| `POSTGRES_PASSWORD` | случайный пароль, используется и в .env, и в compose |
| `PUBLIC_BASE_URL` | `https://levickaya.ru` |
| `FRONTEND_URL`, `YOOKASSA_RETURN_URL`, `CORS_ORIGINS` | задаются в compose из `PUBLIC_BASE_URL` |
| `COURSES_ENABLED` | `false` (первый запуск: только индивидуальные занятия) |
| `EMAIL_PROVIDER` | `resend`; `RESEND_API_KEY` и `EMAIL_FROM` заданы (значения — только в `.env` на сервере) |
| `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY` | пока пустые — до настройки магазина |

Первый администратор: `orkee23@gmail.com`, пароль сгенерирован при деплое и сохранён в
`/root/piano-admin-password` на сервере (передайте его владельцу безопасным каналом и удалите файл).
Старый пользователь `admin@piano-school.local` создан не был: email с доменом `.local`
отклоняется валидатором `email-validator` как зарезервированный.

## Команды

```bash
cd /opt/piano-school
# Все команды compose обязательно передают --env-file .env (иначе подстановка станет пустой).
docker compose --env-file .env -f infra/production/docker-compose.yml ps
docker compose --env-file .env -f infra/production/docker-compose.yml logs -f web api nginx
docker compose --env-file .env -f infra/production/docker-compose.yml exec api uv run --no-dev alembic upgrade head
```

Обновление кода:

```bash
cd /opt/piano-school
git pull
docker compose --env-file .env -f infra/production/docker-compose.yml up -d --build
docker compose --env-file .env -f infra/production/docker-compose.yml exec api uv run --no-dev alembic upgrade head
```

## Проверки после деплоя

```bash
curl -I https://levickaya.ru/                     # 200 от Next.js
curl   https://levickaya.ru/api/health            # {"status":"ok"}
curl -I http://levickaya.ru/                      # 301 на https
ss -tulpn                                          # только 22/80/443 наружу
ufw status verbose
fail2ban-client status
```

## Что осталось сделать до приёма реальных платежей

1. Заполнить ключи ЮKassa, `YOOKASSA_RETURN_URL` и webhook в кабинете: `https://levickaya.ru/api/payments/yookassa/webhook`.
2. Проверить, что домен подтверждён в Resend (SPF/DKIM): переменные уже заданы, но без записей DNS письма могут попадать в спам.
3. Задать финальные цены тарифов 1/4/8 уроков. Юридические страницы и тексты согласий уже
   заполнены (см. `docs/project-foundation.md`, разделы 10–11).
4. Настроить ежедневный бэкап `pgdata` + `redisdata` (например, `pg_dump` в cron + копия на удалённое хранилище).

## Откат при потере SSH

В консоли провайдера (`root` по ключу остаётся) или через VNC:

```bash
mv /etc/ssh/sshd_config.d/10-harden-piano.conf /root/
systemctl reload ssh
ufw disable
```
