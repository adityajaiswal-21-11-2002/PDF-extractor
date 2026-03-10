#!/usr/bin/env bash
set -e
# Reduce memory on free tier (crewai + opentelemetry)
export CREWAI_DISABLE_TELEMETRY=true
export OTEL_SDK_DISABLED=true
# Run Celery worker in background (free tier: no separate worker service)
celery -A app.workers.celery_worker worker --loglevel=info --concurrency=1 &
# Run FastAPI in foreground (keeps container alive)
exec uvicorn main:app --host 0.0.0.0 --port $PORT
