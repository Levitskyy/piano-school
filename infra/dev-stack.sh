#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${TMPDIR:-/tmp}/piano-school"
mkdir -p "$LOG_DIR"
cd "$ROOT_DIR"

echo "→ PostgreSQL и Redis"
docker compose -f infra/docker-compose.yml up -d postgres redis

for _ in $(seq 1 30); do
  if docker compose -f infra/docker-compose.yml exec -T postgres \
    pg_isready -U piano -d piano_school >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -fsS --max-time 2 http://127.0.0.1:8000/health >/dev/null 2>&1; then
  echo "→ FastAPI"
  (
    cd apps/api
    nohup uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload \
      >>"$LOG_DIR/api.log" 2>&1 </dev/null &
  )
fi

if ! curl -fsS --max-time 2 http://127.0.0.1:3000/ >/dev/null 2>&1; then
  echo "→ Next.js"
  nohup pnpm --filter web dev:lan >>"$LOG_DIR/web.log" 2>&1 </dev/null &
fi

for _ in $(seq 1 40); do
  api_ok=0
  web_ok=0
  curl -fsS --max-time 2 http://127.0.0.1:8000/health >/dev/null 2>&1 && api_ok=1
  curl -fsS --max-time 2 http://127.0.0.1:3000/ >/dev/null 2>&1 && web_ok=1
  if [ "$api_ok" = "1" ] && [ "$web_ok" = "1" ]; then
    break
  fi
  sleep 1
done

echo
echo "Сайт:  http://localhost:3000"
echo "API:   http://127.0.0.1:8000/docs"
echo "Логи:  $LOG_DIR/api.log и $LOG_DIR/web.log"
echo "Для доступа из домашней сети: make lan"
