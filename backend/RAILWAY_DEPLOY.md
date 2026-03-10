# Deploy on Railway

### Step 1: Set Root Directory

**Important:** Your repo has a `backend/` folder. In Railway:

1. Open your service → **Settings** → **Source**
2. Set **Root Directory** to `backend`
3. Save

### Step 2: Add environment variables

In **Variables**, add:

| Key | Value |
|-----|-------|
| `PYTHON_VERSION` | `3.12` |
| `DATABASE_URL` | From your `.env` (Aiven) |
| `REDIS_URL` | From your `.env` (Redis Labs) |
| `ENV` | `prod` |
| `EMAIL_FROM` | Your sender email |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | Your Gmail |
| `SMTP_PASSWORD` | Gmail App Password |
| `OPENAI_API_KEY` | Your OpenAI key |
| `SECRET_KEY` | Random string |
| `CREWAI_DISABLE_TELEMETRY` | `true` |
| `OTEL_SDK_DISABLED` | `true` |

### Step 3: Build & Start (auto-detected)

Railway will use `railpack.json` in the backend folder:
- **Build**: `pip install --upgrade pip setuptools && pip install -r requirements.txt`
- **Start**: `bash start.sh`

### Step 4: Deploy

Push to GitHub. Railway will auto-deploy.

---

## If build still fails

Set these in **Settings** → **Build**:
- **Build Command**: `pip install --upgrade pip setuptools && pip install -r requirements.txt`
- **Start Command**: `bash start.sh`
