#!/usr/bin/env bash
set -e
# Run Celery worker in background (free tier: no separate worker service)
celery -A app.workers.celery_worker worker --loglevel=info &
# Run FastAPI in foreground (keeps container alive)
exec uvicorn main:app --host 0.0.0.0 --port $PORT
