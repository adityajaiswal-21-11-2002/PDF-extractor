"""
Test the live Render deployment.
Usage: python test_live.py [BASE_URL]
Default: https://pdf-extractor-l71q.onrender.com
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "https://pdf-extractor-production-0106.up.railway.app"
RECIPIENT_EMAIL = "adityajaiswal1196@gmail.com"  # User email for composed PDF emails
TIMEOUT = 90  # Cold start can take 30-60s on free tier
RESULTS = []


def ok(name, msg="OK"):
    RESULTS.append(("PASS", name, msg))
    print(f"  [PASS] {name}: {msg}")


def fail(name, msg):
    RESULTS.append(("FAIL", name, msg))
    print(f"  [FAIL] {name}: {msg}")


def run():
    print(f"--- Testing live URL: {BASE_URL} ---\n")
    print("(Free tier may take 30-60s on first request after sleep)\n")

    # GET /health
    try:
        start = time.time()
        with urllib.request.urlopen(f"{BASE_URL}/health", timeout=TIMEOUT) as r:
            data = json.loads(r.read().decode())
            elapsed = round(time.time() - start, 1)
            if data.get("status") == "ok":
                ok("GET /health", f"{data.get('version', '')} ({elapsed}s)")
            else:
                fail("GET /health", str(data))
    except urllib.error.URLError as e:
        fail("GET /health", f"{type(e).__name__}: {e.reason}")
    except Exception as e:
        fail("GET /health", str(e))

    # GET /api/health
    try:
        with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=TIMEOUT) as r:
            data = json.loads(r.read().decode())
            if data.get("status") == "ok":
                ok("GET /api/health", data.get("version", ""))
            else:
                fail("GET /api/health", str(data))
    except urllib.error.URLError as e:
        fail("GET /api/health", f"{type(e).__name__}: {e.reason}")
    except Exception as e:
        fail("GET /api/health", str(e))

    # GET / (HTML)
    try:
        with urllib.request.urlopen(f"{BASE_URL}/", timeout=TIMEOUT) as r:
            body = r.read().decode()
            if "AI Agent Orchestrator" in body and "upload" in body.lower():
                ok("GET / (HTML)", "page contains upload form")
            else:
                fail("GET /", "unexpected content")
    except urllib.error.URLError as e:
        fail("GET /", f"{type(e).__name__}: {e.reason}")
    except Exception as e:
        fail("GET /", str(e))

    # HEAD / (Render health check)
    try:
        req = urllib.request.Request(f"{BASE_URL}/", method="HEAD")
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            if r.status == 200:
                ok("HEAD /", "200 OK")
            else:
                fail("HEAD /", f"status {r.status}")
    except urllib.error.HTTPError as e:
        if e.code == 405:
            fail("HEAD /", "405 Method Not Allowed")
        else:
            fail("HEAD /", f"HTTP {e.code}")
    except urllib.error.URLError as e:
        fail("HEAD /", f"{type(e).__name__}: {e.reason}")
    except Exception as e:
        fail("HEAD /", str(e))

    # POST /api/upload with valid PDF
    pdf_path = os.path.join(os.path.dirname(__file__), "tests", "sample.pdf")
    if not os.path.isfile(pdf_path):
        fail("POST /api/upload (PDF)", "tests/sample.pdf not found")
    else:
        try:
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
            boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
            body = (
                f"--{boundary}\r\n"
                'Content-Disposition: form-data; name="file"; filename="sample.pdf"\r\n'
                "Content-Type: application/pdf\r\n\r\n"
            ).encode() + pdf_data + f"\r\n--{boundary}--\r\n".encode()
            req = urllib.request.Request(
                f"{BASE_URL}/api/upload?recipient_email={RECIPIENT_EMAIL}",
                data=body,
                method="POST",
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read().decode())
                if "job_id" in data and "status" in data:
                    ok("POST /api/upload (PDF)", f"job_id={data['job_id']} status={data['status']}")
                    job_id = data["job_id"]
                    try:
                        with urllib.request.urlopen(f"{BASE_URL}/api/jobs/{job_id}", timeout=5) as r2:
                            job = json.loads(r2.read().decode())
                            if "id" in job and "status" in job:
                                ok("GET /api/jobs/{id}", f"status={job['status']}")
                            else:
                                fail("GET /api/jobs/{id}", str(job))
                    except Exception as e2:
                        fail("GET /api/jobs/{id}", str(e2))
                else:
                    fail("POST /api/upload (PDF)", str(data))
        except urllib.error.HTTPError as e:
            fail("POST /api/upload (PDF)", f"HTTP {e.code} {e.reason}")
        except urllib.error.URLError as e:
            fail("POST /api/upload (PDF)", f"{type(e).__name__}: {e.reason}")
        except Exception as e:
            fail("POST /api/upload (PDF)", str(e))

    # POST /api/upload invalid type (expect 400/422)
    try:
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="x.txt"\r\n'
            "Content-Type: text/plain\r\n\r\n"
            "hello\r\n"
            f"--{boundary}--\r\n"
        ).encode()
        req = urllib.request.Request(
            f"{BASE_URL}/api/upload?recipient_email={RECIPIENT_EMAIL}",
            data=body,
            method="POST",
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        urllib.request.urlopen(req, timeout=TIMEOUT)
        fail("POST /api/upload (invalid type)", "expected 400/422, got 2xx")
    except urllib.error.HTTPError as e:
        if e.code in (400, 422):
            ok("POST /api/upload (invalid type)", f"rejected with {e.code}")
        else:
            fail("POST /api/upload (invalid type)", f"got {e.code}")
    except urllib.error.URLError as e:
        fail("POST /api/upload (invalid type)", f"{type(e).__name__}: {e.reason}")
    except Exception as e:
        fail("POST /api/upload (invalid type)", str(e))

    passed = sum(1 for r in RESULTS if r[0] == "PASS")
    failed = sum(1 for r in RESULTS if r[0] == "FAIL")
    print(f"\n=== Result: {passed} passed, {failed} failed ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run())
