# Как разрабатывать и вливать изменения

## Правило: в `master` только через Pull Request

Прямые коммиты в `master` не делаем. Одна задача = одна ветка = один PR.

```bash
# 1. Обновляем локальный master
git checkout master
git pull origin master

# 2. Ветка под задачу
git checkout -b fix/payment-webhook

# 3. Правим код, проверяем локально
make check            # ruff + pytest + ESLint + typecheck

# 4. Коммит и пуш ветки
git add .
git commit -m "Fix webhook signature validation"
git push -u origin fix/payment-webhook
```

Дальше на GitHub открываете **Pull Request** `fix/payment-webhook → master`.
В PR автоматически запускается `.github/workflows/ci.yml`: ruff, pytest, ESLint, typecheck и сборка Next.js.
Мердж разрешён только после зелёных проверок (branch protection включён).

## Что происходит после мерджа

Workflow `.github/workflows/deploy.yml`:
1. снова прогоняет проверки на коммите из `master`;
2. по SSH подключается к `193.233.88.115`;
3. делает `git checkout <sha>` (тот самый проверенный коммит);
4. `docker compose up -d --build` — пересобирает изменённые образы и перезапускает сервисы;
5. применяет миграции `alembic upgrade head`.

Файлы `.env`, TLS-сертификат (`infra/production/selfsigned.*` — копия сертификата Let's Encrypt) и логи находятся в `.gitignore` и при деплое не перезаписываются.

Следить за деплоем: **GitHub → Actions → Deploy to VPS**.

## Важное

- **Секреты** для деплоя уже добавлены в настройках репозитория (Settings → Secrets and variables → Actions):
  `VPS_SSH_KEY`. Хост, пользователь и порт прописаны в workflow явно.
- Если вы добавляете новую env-переменную: сначала допишите её в `.env.example` и `infra/production/.env.example`,
  потом на сервере добавьте в `/opt/piano-school/.env` **до** мерджа — иначе сервис может не подняться.
- Если меняете `docker-compose.yml` или `nginx.conf`, деплой сам перезапустит nginx и остальные сервисы.
- Ветку после мерджа можно удалить (кнопка на GitHub или `git branch -d <branch>` локально).

## Если GitHub недоступен из браузера

Проверить деплой можно прямо с сервера:

```bash
ssh root@193.233.88.115
cd /opt/piano-school
git rev-parse HEAD        # должен совпадать с последним коммитом master
docker compose --env-file .env -f infra/production/docker-compose.yml ps
```

## Откат

Если деплой сломал прод:

```bash
ssh root@193.233.88.115
cd /opt/piano-school
git log --oneline -5          # найти предыдущий рабочий sha
git checkout <хороший-sha>
docker compose --env-file .env -f infra/production/docker-compose.yml up -d --build
```

Или через GitHub: revert-коммит в `master` → автодеплой откатится к предыдущему состоянию.
