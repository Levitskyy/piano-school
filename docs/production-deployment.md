# Продакшен на VPS (193.233.88.115)

Текущее состояние: домен `levickaya.ru` подключён, HTTPS работает с сертификатом Let's Encrypt для `levickaya.ru` и `www.levickaya.ru` (`curl -I https://levickaya.ru/` → 200). `PUBLIC_BASE_URL=https://levickaya.ru`, письма отправляются через Resend. По старому IP браузер по-прежнему покажет предупреждение о сертификате — используйте домен.

Тестовый платёж через ЮKassa проведён 25.11.2026: заказ `aadbc860-c401-4de0-a3d8-0a890a882064`, статус `succeeded`, запись и пакет созданы. Подробности — в разделе «Проверенный тестовый платёж» ниже.

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
    selfsigned.{crt,key}      # имя историческое: внутри лежит текущий сертификат Let's Encrypt
/etc/letsencrypt/              # certbot: live/archive/renewal + renewal-hooks
/var/www/certbot/              # webroot для HTTP-01 при обновлении
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
| `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY`, `YOOKASSA_RETURN_URL` | заполнены; тестовый платёж 25.11.2026 прошёл |
| `PRODAMUS_FORM_URL`, `PRODAMUS_SECRET_KEY`, `PRODAMUS_PAYMENT_METHOD`, `PRODAMUS_CURRENCY` | в `.env` пока не заданы; действуют дефолты `https://payform.ru/`, `monetaworld`, `rub`, пустой секретный ключ |

Первый администратор: `orkee23@gmail.com`, пароль сгенерирован при деплое и сохранён в
`/root/piano-admin-password` на сервере (передайте его владельцу безопасным каналом и удалите файл).
Старый пользователь `admin@piano-school.local` удалён с прода 24.11.2026: email с доменом
`.local` отклоняется валидатором `email-validator` как зарезервированный, из-за чего
`GET /admin/users` отвечал 500. Новые такие аккаунты регистрация не принимает.

## TLS

Сертификат выпущен через `certbot certonly --standalone` (HTTP-01, порт 80 на время выпуска
был освобождён остановкой nginx-контейнера). Действует до **22.02.2027**, обновляется
`certbot.timer` (два раза в день, реально — за 30 дней до expires).

Хуки обновления в `/etc/letsencrypt/renewal-hooks/`:

- `pre/10-stop-nginx.sh` — остановить nginx-контейнер (standalone снова займёт :80);
- `deploy/10-copy-cert.sh` — скопировать `fullchain.pem`/`privkey.pem` в `infra/production/selfsigned.*`
  (`cp`, а не `install`, чтобы сохранить inode bind-монта);
- `post/10-start-nginx.sh` — поднять nginx обратно.

Проверить обновление: `certbot renew --dry-run`. Текущий сертификат:
`certbot certificates`.

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
curl -I https://levickaya.ru/                      # 200 от Next.js, сертификат без предупреждений
curl    https://levickaya.ru/api/health            # {"status":"ok"}
curl -I http://levickaya.ru/                       # 301 на https
certbot certificates                               # срок действия сертификата
ss -tulpn                                          # только 22/80/443 наружу
ufw status verbose
fail2ban-client status
```

## Проверенный тестовый платёж (25.11.2026)

- Заказ `aadbc860-c401-4de0-a3d8-0a890a882064`, провайдер `yookassa`, сумма **1 ₽**:
  тариф `single` 1500 ₽ с промокодом `CHECK` (99.9%). Платёж ЮKassa
  `329939f0-000f-5001-9000-19ea40cd3735`, статус `succeeded`.
- Четыре HTTP-уведомления пришли с официальных IP `77.75.153.78` и `77.75.154.206`,
  все получили `204 No Content`. Повторные уведомления не создали дубликатов: запись
  и пакет созданы по одному разу.
- Слот `2026-11-28 08:00 UTC` подтверждён, пакет из 1 урока создан, остаток 0.
- В логах `api`, `worker` и `nginx` за период платежа нет `403`, `502` и traceback.
  Были только сканирующие запросы к `/.env` и `/.git/config` — оба вернули `404`.

## Что осталось сделать до приёма реальных платежей

1. [x] ЮKassa: ключи и webhook настроены, тестовый платёж принят и выдал доступ.
2. [ ] Подтвердить порядок чеков для НПД. Тестовый платёж прошёл, но код не передаёт
   `receipt`/`tax_system_code`; нужно зафиксировать, формируется ли чек в кабинете ЮKassa
   или самозанятый выдаёт его через «Мой налог». До первого реального платежа.
3. [ ] Подтвердить финальность цен в БД: `single` 1500 ₽, `package-4` 5899 ₽,
   `package-8` 11499 ₽. Тестовый промокод `CHECK` уже использован.
4. [x] Prodamus: ключи заданы, webhook и тестовый платёж работают. Ссылка оплаты отправляется
   с `callbackType=json`, `payment_method=monetaworld`, `currency=rub` и `urlSuccess`
   (`/payment/success?order_num=<id заказа>`), подпись `Sign` проверяется до выдачи доступа.
   Глобальный SuccessURL в кабинете можно оставить, но код передаёт `urlSuccess` явно.
   Перед реальными платежами получить в поддержке письменное подтверждение приёма карт США
   для плательщика НПД.
5. [ ] Проверить, что домен подтверждён в Resend (SPF/DKIM): переменные уже заданы, но без записей DNS письма могут попадать в спам.
6. [ ] Настроить ежедневный бэкап `pgdata` + `redisdata` (например, `pg_dump` в cron + копия на удалённое хранилище).
7. [ ] Убрать `X-Robots-Tag: noindex` и увеличить HSTS в `nginx.conf` (отдельным PR).

## Откат при потере SSH

В консоли провайдера (`root` по ключу остаётся) или через VNC:

```bash
mv /etc/ssh/sshd_config.d/10-harden-piano.conf /root/
systemctl reload ssh
ufw disable
```
