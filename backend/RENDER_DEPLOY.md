# Step-by-Step: Deploy on Render

Deploy the AI Agent Orchestration Backend on Render (100% free tier).

---

## Path A: Use Render's PostgreSQL + Redis (Blueprint)

### Step 1: Push code to GitHub

1. Open your project folder in a terminal.
2. If not already a git repo: `git init`
3. Add and commit:
   ```bash
   git add .
   git commit -m "Deploy to Render"
   ```
4. Create a repo on [github.com](https://github.com/new) (e.g. `PDF-extractor`).
5. Push:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Sign up / log in to Render

1. Go to [render.com](https://render.com)
2. Click **Get Started** or **Log In**
3. Sign in with GitHub

### Step 3: Create a Blueprint

1. In the Render dashboard, click **New +** (top right)
2. Select **Blueprint**
3. Click **Connect a repository**
4. Choose your GitHub repo (e.g. `PDF-extractor`)
5. Set **Blueprint Path** to: `backend/render.yaml`
   - If your repo root is the backend folder (no `backend/` subfolder), use `render.yaml` and remove `rootDir: backend` from `render.yaml` first.
6. Click **Apply**

### Step 4: Enter environment variables

When Render shows the setup screen, it will ask for values for `sync: false` variables. Enter:

| Variable | Value |
|----------|-------|
| **EMAIL_FROM** | Your sender email |
| **SMTP_HOST** | `smtp.gmail.com` |
| **SMTP_USER** | Your Gmail address |
| **SMTP_PASSWORD** | Your [Gmail App Password](https://support.google.com/accounts/answer/185833) |
| **OPENAI_API_KEY** | Your OpenAI API key |

Click **Apply** or **Create** to start the deployment.

### Step 5: Wait for deployment

1. Render will create PostgreSQL, Redis, and the web service.
2. Watch the **Logs** tab for the `agent-api` service.
3. Wait until you see something like: `Uvicorn running on http://0.0.0.0:XXXX`

### Step 6: Test your app

1. Open the URL shown for `agent-api` (e.g. `https://agent-api-xxxx.onrender.com`)
2. Visit `/` – you should see the PDF upload page
3. Visit `/health` – should return `{"status":"ok"}`
4. Upload a PDF and check job status at `/api/v1/jobs/{job_id}`

---

## Path B: Use your existing Aiven + Redis Labs

If you already use Aiven PostgreSQL and Redis Labs, skip Render’s database and Redis and wire your app to your existing services.

### Step 1–2: Same as Path A

Push to GitHub and sign in to Render.

### Step 3: Create only the Web Service (no Blueprint)

1. In the Render dashboard, click **New +** → **Web Service**
2. Connect your GitHub repo
3. Configure:
   - **Name**: `agent-api`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Root Directory**: `backend` (if your backend is in a `backend/` folder)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `bash start.sh`
   - **Instance Type**: Free

### Step 4: Add environment variables

1. In the Web Service settings, open **Environment**
2. Click **Add Environment Variable**
3. Add these one by one:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Copy from your `.env` or build: `postgresql://USER:PASSWORD@HOST:PORT/DBNAME` |
| `REDIS_URL` | Copy from your `.env` (e.g. `redis://default:PASSWORD@HOST:PORT/0`) |
| `ENV` | `prod` |
| `EMAIL_BACKEND` | `smtp` |
| `EMAIL_FROM` | `aj8750323339@gmail.com` |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | Your Gmail address |
| `SMTP_PASSWORD` | Your Gmail App Password |
| `OPENAI_API_KEY` | Your OpenAI API key |
| `SECRET_KEY` | Any random string (e.g. `my-secret-key-12345`) |

4. Save changes

### Step 5: Allow external connections (Aiven / Redis Labs)

1. **Aiven**: In the Aiven dashboard, ensure your PostgreSQL allows connections from Render’s IPs (or use “Allow all” for testing).
2. **Redis Labs**: In Redis Labs, ensure the database allows public access or add Render’s IPs to the allow list.

### Step 6: Deploy and test

1. Click **Manual Deploy** → **Deploy latest commit**
2. Wait for the build and deploy to finish
3. Open the service URL and test `/`, `/health`, and PDF upload as in Path A

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Build fails | Check **Logs** for errors; ensure `requirements.txt` and `start.sh` exist in the root directory (or `backend/` if using Root Directory) |
| 503 / app not responding | Free tier sleeps after ~15 min; first request can take 30–60 seconds |
| Database connection error | Check `DATABASE_URL` format; Aiven must allow connections from Render |
| Redis connection error | Check `REDIS_URL`; Redis Labs must allow connections from Render |
| Email not sending | Use a [Gmail App Password](https://support.google.com/accounts/answer/185833), not your normal password |

---

## Quick reference

- **App URL**: `https://<service-name>.onrender.com`
- **Health check**: `https://<service-name>.onrender.com/health`
- **API docs**: `https://<service-name>.onrender.com/docs`
