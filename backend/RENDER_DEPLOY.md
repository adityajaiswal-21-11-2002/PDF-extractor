# Step-by-Step: Deploy on Render (Aiven + Redis Labs)

Deploy using your existing Aiven PostgreSQL and Redis Labs.

---

### Step 1: Push code to GitHub

1. In your project folder:
   ```bash
   git add .
   git commit -m "Deploy to Render"
   git push origin main
   ```

### Step 2: Sign in to Render

1. Go to [render.com](https://render.com) and sign in with GitHub

### Step 3: Create Web Service

1. Click **New +** → **Web Service**
2. Connect your GitHub repo
3. Configure:
   - **Name**: `agent-api`
   - **Root Directory**: `backend`
   - **Build Command**: `pip install --upgrade pip setuptools && pip install -r requirements.txt`
   - **Start Command**: `bash start.sh`
   - **Instance Type**: Free

### Step 4: Add environment variables

In **Environment** → **Add Environment Variable**, add:

| Key | Value |
|-----|-------|
| `PYTHON_VERSION` | `3.12.0` *(required – Render defaults to 3.14)* |
| `DATABASE_URL` | From your `.env` (Aiven connection string) |
| `REDIS_URL` | From your `.env` (Redis Labs connection string) |
| `ENV` | `prod` |
| `EMAIL_BACKEND` | `smtp` |
| `EMAIL_FROM` | Your sender email |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | Your Gmail address |
| `SMTP_PASSWORD` | Gmail App Password |
| `OPENAI_API_KEY` | Your OpenAI API key |
| `SECRET_KEY` | Any random string |

### Step 5: Allow external connections

1. **Aiven**: In the Aiven dashboard, allow connections from anywhere (or add Render’s IPs)
2. **Redis Labs**: In Redis Labs, ensure the database allows public access

### Step 6: Deploy and test

1. Click **Create Web Service** (or **Manual Deploy** if already created)
2. Wait for the build to finish
3. Open the service URL → `/` for upload, `/health` for health check

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: No module named 'pkg_resources'` | Set **Build Command** to `pip install --upgrade pip setuptools && pip install -r requirements.txt`. If using cached build, trigger **Clear build cache & deploy** |
| Build fails | Check **Logs**; ensure `requirements.txt` and `start.sh` exist in `backend/` |
| 503 / app not responding | Free tier sleeps after ~15 min; first request can take 30–60 seconds |
| Database connection error | Check `DATABASE_URL`; Aiven must allow connections from Render |
| Redis connection error | Check `REDIS_URL`; Redis Labs must allow public access |
| Email not sending | Use a [Gmail App Password](https://support.google.com/accounts/answer/185833) |

---

## Quick reference

- **App**: `https://<service-name>.onrender.com`
- **Health**: `https://<service-name>.onrender.com/health`
- **API docs**: `https://<service-name>.onrender.com/docs`
