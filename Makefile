.DEFAULT_GOAL := help

.PHONY: help install dev-stack dev-api dev-web dev-web-lan lan db-up db-down migrate revision role grant-access seed-demo lint test check

help:
	@echo "install      — установить зависимости web и api"
	@echo "dev-stack    — поднять БД, API и web в фоне (для проверки с телефона)"
	@echo "dev-api      — запустить FastAPI с авторелоадом (порт 8000)"
	@echo "dev-web      — запустить Next.js (порт 3000, только localhost)"
	@echo "dev-web-lan  — запустить Next.js для доступа из домашней сети"
	@echo "lan          — пробросить порт Windows -> WSL (нужен UAC)"
	@echo "db-up        — поднять PostgreSQL и Redis в Docker"
	@echo "db-down      — остановить PostgreSQL и Redis"
	@echo "migrate      — применить миграции Alembic"
	@echo "revision     — создать миграцию: make revision m=\"message\""
	@echo "role         — сменить роль: make role email=... role=admin"
	@echo "grant-access — выдать курс: make grant-access email=... course=... offer=..."
	@echo "seed-demo    — создать демонстрационный курс"
	@echo "lint         — Ruff + ESLint"
	@echo "test         — pytest"
	@echo "check        — lint + test + typecheck"

install:
	pnpm install
	cd apps/api && uv sync

dev-stack:
	@bash infra/dev-stack.sh

dev-api:
	cd apps/api && uv run uvicorn app.main:app --reload --port 8000

dev-web:
	pnpm --filter web dev

dev-web-lan:
	pnpm --filter web dev:lan

lan:
	/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$$(wslpath -w infra/windows-lan.ps1)"

db-up:
	docker compose -f infra/docker-compose.yml up -d postgres redis

db-down:
	docker compose -f infra/docker-compose.yml down

migrate:
	cd apps/api && uv run alembic upgrade head

revision:
	cd apps/api && uv run alembic revision --autogenerate -m "$(m)"

role:
	cd apps/api && uv run python -m app.manage set-role --email "$(email)" --role "$(role)"

grant-access:
	cd apps/api && uv run python -m app.manage grant-access --email "$(email)" --course "$(course)" --offer "$(offer)"

seed-demo:
	cd apps/api && uv run python -m app.manage seed-demo-course

lint:
	cd apps/api && uv run ruff check .
	pnpm --filter web lint

test:
	cd apps/api && uv run pytest

check: lint test
	pnpm --filter web typecheck
