FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --upgrade pip setuptools && pip install -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for Celery (avoids security warning)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Railway/Render uses PORT env var
ENV PORT=8080
EXPOSE $PORT

USER appuser

CMD ["bash", "start.sh"]
