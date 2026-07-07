#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Waiting for database to become available..."
python - <<'PY'
import os
import time
import psycopg2

url = os.getenv("DATABASE_URL", "")
if not url:
    raise RuntimeError("DATABASE_URL is not set")

attempts = int(os.getenv("DB_STARTUP_MAX_ATTEMPTS", "30"))
delay = float(os.getenv("DB_STARTUP_DELAY_SECONDS", "2"))

for i in range(1, attempts + 1):
    try:
        conn = psycopg2.connect(url)
        conn.close()
        print(f"[entrypoint] Database ready after attempt {i}.")
        break
    except Exception as exc:
        if i == attempts:
            raise RuntimeError(
                f"Database was not ready after {attempts} attempts"
            ) from exc
        print(f"[entrypoint] DB not ready (attempt {i}/{attempts}): {exc}")
        time.sleep(delay)
PY

echo "[entrypoint] Running Alembic migrations..."
python -m alembic upgrade head

echo "[entrypoint] Starting API server..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
