"""
Run all application tests: config, DB, Redis, and API (health, upload, job status, errors).
Starts uvicorn in a subprocess, runs HTTP tests, then shuts down.
"""
import os
import subprocess
import sys
import time

# Ensure backend root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "http://127.0.0.1:8000"
SERVER_START_TIMEOUT = 25
RESULTS = []


def ok(name, msg="OK"):
    RESULTS.append(("PASS", name, msg))
    print(f"  [PASS] {name}: {msg}")


def fail(name, msg):
    RESULTS.append(("FAIL", name, msg))
    print(f"  [FAIL] {name}: {msg}")


def check_config():
    print("\n--- Config ---")
    try:
        from app.core.config import settings
        db = str(settings.SQLALCHEMY_DATABASE_URI)
        # Redact password
        if "@" in db:
            db = db.split("@")[1] if "@" in db else db
        print(f"  DB (host): {db}")
        print(f"  REDIS_URL: {settings.REDIS_URL[:50]}...")
        ok("config", "settings loaded")
    except Exception as e:
        fail("config", str(e))


def check_db():
    print("\n--- Database ---")
    try:
        from app.database.session import engine
        conn = engine.connect()
        conn.close()
        ok("database", "connection OK")
    except Exception as e:
        fail("database", str(e))


def check_redis():
    print("\n--- Redis ---")
    try:
        from app.core.config import settings
        import redis
        r = redis.Redis.from_url(settings.REDIS_URL)
        r.ping()
        ok("redis", "connection OK")
    except Exception as e:
        fail("redis", str(e))


def ensure_tables():
    """Create DB tables if they don't exist (so upload can succeed)."""
    try:
        from app.database.base import Base
        from app.database.session import engine
        # Import models so they register with Base
        from app.models import user, document, job, agent_output, email_record, execution_log  # noqa: F401
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        pass  # non-fatal; upload may still work if tables exist


def start_server():
    print("\n--- Starting API server ---")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        env=os.environ.copy(),
    )
    return proc


def wait_for_server():
    import urllib.request
    import urllib.error
    start = time.time()
    while time.time() - start < SERVER_START_TIMEOUT:
        try:
            urllib.request.urlopen(f"{BASE_URL}/health", timeout=2)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def run_http_tests():
    import urllib.request
    import urllib.error
    import urllib.parse
    import json

    print("\n--- HTTP tests ---")

    # GET /health
    try:
        req = urllib.request.Request(f"{BASE_URL}/health")
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            if data.get("status") == "ok":
                ok("GET /health", data.get("version", ""))
            else:
                fail("GET /health", str(data))
    except Exception as e:
        fail("GET /health", str(e))

    # GET /api/health
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/health")
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            if data.get("status") == "ok":
                ok("GET /api/health", data.get("version", ""))
            else:
                fail("GET /api/health", str(data))
    except Exception as e:
        fail("GET /api/health", str(e))

    # GET / (HTML)
    try:
        req = urllib.request.Request(f"{BASE_URL}/")
        with urllib.request.urlopen(req, timeout=5) as r:
            body = r.read().decode()
            if "AI Agent Orchestrator" in body and "upload" in body.lower():
                ok("GET / (HTML)", "page contains upload form")
            else:
                fail("GET /", "unexpected content")
    except Exception as e:
        fail("GET /", str(e))

    # POST /api/upload with invalid file type first (expect 400/422) - fast
    try:
        import requests
        r = requests.post(
            f"{BASE_URL}/api/upload",
            params={"recipient_email": "test@example.com"},
            files={"file": ("x.txt", b"hello", "text/plain")},
            timeout=15,
        )
        if r.status_code in (400, 422):
            ok("POST /api/upload (invalid type)", f"rejected with {r.status_code}")
        else:
            fail("POST /api/upload (invalid type)", f"got {r.status_code}, expected 400/422")
    except Exception as e:
        fail("POST /api/upload (invalid type)", str(e))

    # POST /api/upload with valid PDF (use a minimal valid PDF so test is reliable)
    try:
        import requests
        from io import BytesIO
        from pypdf import PdfWriter
        buf = BytesIO()
        w = PdfWriter()
        w.add_blank_page(width=100, height=100)
        w.write(buf)
        pdf_bytes = buf.getvalue()
        r = requests.post(
            f"{BASE_URL}/api/upload",
            params={"recipient_email": "test@example.com"},
            files={"file": ("sample.pdf", pdf_bytes, "application/pdf")},
            timeout=120,
        )
        if r.status_code == 202:
            data = r.json()
            if "job_id" in data and "status" in data:
                ok("POST /api/upload (PDF)", f"job_id={data['job_id']} status={data['status']}")
                job_id = data["job_id"]
                try:
                    r2 = requests.get(f"{BASE_URL}/api/jobs/{job_id}", timeout=10)
                    r2.raise_for_status()
                    job = r2.json()
                    if "id" in job and "status" in job:
                        ok("GET /api/jobs/{id}", f"status={job['status']}")
                    else:
                        fail("GET /api/jobs/{id}", str(job))
                except Exception as e2:
                    fail("GET /api/jobs/{id}", str(e2))
            else:
                fail("POST /api/upload (PDF)", str(data))
        else:
            fail("POST /api/upload (PDF)", f"HTTP {r.status_code} {r.text[:200]}")
    except Exception as e:
        fail("POST /api/upload (PDF)", str(e))



def main():
    global RESULTS
    RESULTS = []
    print("=== Application test suite ===")
    check_config()
    check_db()
    check_redis()
    proc = None
    try:
        ensure_tables()
        proc = start_server()
        if not wait_for_server():
            fail("server", "did not start in time")
        else:
            ok("server", "started")
            run_http_tests()
        passed = sum(1 for r in RESULTS if r[0] == "PASS")
        failed = sum(1 for r in RESULTS if r[0] == "FAIL")
    finally:
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            if proc.stderr and RESULTS:
                _failed = sum(1 for r in RESULTS if r[0] == "FAIL")
                if _failed > 0:
                    try:
                        err = proc.stderr.read().decode(errors="replace")
                        if err:
                            print("\n--- Server stderr (last 2000 chars) ---")
                            print(err[-2000:] if len(err) > 2000 else err)
                    except Exception:
                        pass
            print("\n--- Server stopped ---")
    passed = sum(1 for r in RESULTS if r[0] == "PASS")
    failed = sum(1 for r in RESULTS if r[0] == "FAIL")
    print(f"\n=== Result: {passed} passed, {failed} failed ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
