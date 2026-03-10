# Use this when building from repo root (no Root Directory set)
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --upgrade pip setuptools && pip install -r requirements.txt

COPY backend/ .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

ENV PORT=8080
EXPOSE $PORT

USER appuser

CMD ["bash", "start.sh"]
