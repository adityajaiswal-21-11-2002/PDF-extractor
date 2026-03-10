# Use this when building from repo root (no Root Directory set)
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --upgrade pip setuptools && pip install -r requirements.txt

COPY backend/ .

ENV PORT=8080
EXPOSE $PORT

CMD ["bash", "start.sh"]
