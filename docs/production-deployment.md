# Продакшен на VPS (193.233.88.115)

Текущее состояние: домен `levickaya.ru` подключён, HTTPS работает с сертификатом Let's Encrypt для `levickaya.ru` и `www.levickaya.ru` (`curl -I https://levickaya.ru/` → 200). `PUBLIC_BASE_URL=https://levickaya.ru`, письма отправляются через Resend. По старому IP браузер по-прежнему покажет предупреждение о сертификате — используйте домен.

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
| `YOOKASSA_SHOP_ID`, `YOOKASSA_SECRET_KEY` | пока пустые — до настройки магазина |
| `PRODAMUS_FORM_URL`, `PRODAMUS_SECRET_KEY`, `PRODAMUS_PAYMENT_METHOD`, `PRODAMUS_CURRENCY` | пока пустые — до настройки платёжной формы; значения передаются в api/worker через env_file |

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

## Что осталось сделать до приёма реальных платежей

1. Заполнить ключи ЮKassa, `YOOKASSA_RETURN_URL` и webhook в кабинете: `https://levickaya.ru/api/payments/yookassa/webhook`. Уведомления не подписаны: API проверяет IP из официального списка и статус платежа GET-запросом.
2. Заполнить `PRODAMUS_*` из кабинета платёжной формы. В настройках указать URL уведомлений `https://levickaya.ru/api/payments/prodamus/webhook`, SuccessURL `https://levickaya.ru/payment/success`, тот же секретный ключ и схему чеков для самозанятого. Ссылка оплаты отправляется с `callbackType=json`, `payment_method=monetaworld` и `currency=rub`; подпись `Sign` проверяется до выдачи доступа. Перед реальными платежами получить в поддержке письменное подтверждение приёма карт США для плательщика НПД по этому сценарию.
3. Проверить, что домен подтверждён в Resend (SPF/DKIM): переменные уже заданы, но без записей DNS письма могут попадать в спам.
4. Задать финальные цены тарифов 1/4/8 уроков. Юридические страницы и тексты согласий уже
   заполнены (см. `docs/project-foundation.md`, разделы 10–11).
5. Настроить ежедневный бэкап `pgdata` + `redisdata` (например, `pg_dump` в cron + копия на удалённое хранилище).
6. Убрать `X-Robots-Tag: noindex` и увеличить HSTS в `nginx.conf` (отдельным PR).

## Откат при потере SSH

В консоли провайдера (`root` по ключу остаётся) или через VNC:

```bash
mv /etc/ssh/sshd_config.d/10-harden-piano.conf /root/
systemctl reload ssh
ufw disable
```
