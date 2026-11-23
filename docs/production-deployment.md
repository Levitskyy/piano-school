# Продакшен на VPS (193.233.88.115)

Текущее состояние: домена нет, HTTPS на самоподписанном сертификате (в браузере будет предупреждение). При появлении домена сертификат меняется на Let's Encrypt и `PUBLIC_BASE_URL` обновляется на `https://...`.

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
| `PUBLIC_BASE_URL` | `https://193.233.88.115` |
| `FRONTEND_URL`, `YOOKASSA_RETURN_URL`, `CORS_ORIGINS` | задаются в compose из `PUBLIC_BASE_URL` |
| `COURSES_ENABLED` | `false` (первый запуск: только индивидуальные занятия) |
| `EMAIL_PROVIDER` | пока `console`; для сброса пароля в проде нужен Unisender Go |
| `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY` | пока пустые — до настройки магазина |

## Команды

```bash
cd /opt/piano-school
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
curl -kI https://193.233.88.115/                  # 200 от Next.js
curl -k  https://193.233.88.115/api/health        # {"status":"ok"}
curl -kI http://193.233.88.115/                   # 301 на https
ss -tulpn                                          # только 22/80/443 наружу
ufw status verbose
fail2ban-client status
```

## Что осталось сделать до приёма реальных платежей

1. Подключить домен, выпустить сертификат Let's Encrypt (certbot), убрать self-signed и `X-Robots-Tag`.
2. Заполнить ключи ЮKassa, `YOOKASSA_RETURN_URL` и webhook в кабинете: `https://<домен>/api/payments/yookassa/webhook`.
3. Настроить Unisender Go (SPF/DKIM) и `EMAIL_PROVIDER=unisender`, `EMAIL_FROM`, `UNISENDER_API_KEY`.
4. Заполнить юридические страницы и цены (см. чек-лист в `docs/project-foundation.md`, раздел 10).
5. Настроить ежедневный бэкап `pgdata` + `redisdata` (например, `pg_dump` в cron + копия на удалённое хранилище).

## Откат при потере SSH

В консоли провайдера (`root` по ключу остаётся) или через VNC:

```bash
mv /etc/ssh/sshd_config.d/10-harden-piano.conf /root/
systemctl reload ssh
ufw disable
```
