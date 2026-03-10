# Deploy on Railway

### Step 1: Root Directory (choose one)

**Option A – Root Directory = `backend`**  
1. Settings → Source → **Root Directory** = `backend`  
2. Railway will use `backend/Dockerfile` and `backend/requirements.txt`

**Option B – No Root Directory**  
1. Leave Root Directory empty  
2. Railway will use the `Dockerfile` at repo root (builds from `backend/`)

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
| `LLM_PROVIDER` | `groq` (default), `openai`, or `gemini` |
| `GROQ_API_KEY` | Free at [console.groq.com](https://console.groq.com) (required when LLM_PROVIDER=groq) |
| `OPENAI_API_KEY` | Your OpenAI key (when LLM_PROVIDER=openai) |
| `GOOGLE_API_KEY` | Free at [aistudio.google.com](https://aistudio.google.com/apikey) (when LLM_PROVIDER=gemini) |
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

## Troubleshooting

### `401 - Incorrect API key provided` (OpenAI)

PDF jobs fail with `openai.AuthenticationError: Error code: 401 - Incorrect API key provided`.

**Fix:** Use a valid OpenAI key, or switch to a **free** alternative:

| Provider | Free? | Get key |
|----------|-------|---------|
| **Groq** | Yes | [console.groq.com](https://console.groq.com) |
| **Gemini** | Yes | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |

Set `LLM_PROVIDER=groq` and `GROQ_API_KEY=your_key` (or `gemini` + `GOOGLE_API_KEY`), then redeploy.

**If staying with OpenAI:**
1. Go to [OpenAI API Keys](https://platform.openai.com/account/api-keys)
2. Create a **new** API key (old keys may be revoked or expired)
3. In Railway → **Variables** → set `OPENAI_API_KEY` to the new key
4. Redeploy

---

## If build still fails

Set these in **Settings** → **Build**:
- **Build Command**: `pip install --upgrade pip setuptools && pip install -r requirements.txt`
- **Start Command**: `bash start.sh`
