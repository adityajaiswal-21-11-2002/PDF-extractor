FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --upgrade pip setuptools && pip install -r requirements.txt

# Copy application code
COPY . .

# Railway/Render uses PORT env var
ENV PORT=8080
EXPOSE $PORT

CMD ["bash", "start.sh"]
