## AI Agent Orchestration Backend

Production-grade backend for an AI Agent Orchestration platform built with **FastAPI**, **CrewAI**, **LangChain**, **PostgreSQL**, **SQLAlchemy**, **Redis**, and **Celery**. The system ingests PDFs, runs a multi-agent workflow to extract structure and generate contextual professional emails, and delivers them via SMTP or SendGrid with full execution tracing.

### High-Level Architecture

- **API Layer (FastAPI)**: Exposes REST endpoints for PDF upload, job status, document/email listing, and health checks.
- **Agent Orchestration Layer (CrewAI + LangChain)**: Coordinates three agents:
  - PDF Analyzer Agent
  - Email Composer Agent
  - Email Delivery Validator Agent
- **Tooling Layer**: PDF parsing (`pypdf`), email templates, retry utilities.
- **Persistence Layer (PostgreSQL + SQLAlchemy)**: Normalized models for users, documents, processing jobs, agent outputs, email records, and execution logs.
- **Background Processing (Celery + Redis)**: Offloads heavy agent workflows, supports retries and backoff, and prevents duplicate processing.
- **Email Infrastructure**: SMTP or SendGrid based on configuration, with delivery status stored in the database.
- **Observability**: Structured JSON logging with Loguru, execution logs in DB, ready for integration with metrics backends.

### Architecture Diagram

```text
           +-------------------+
           |   Client / UI     |
           +---------+---------+
                     |
                     | HTTP (REST)
                     v
          +----------+-----------+
          |      FastAPI API     |
          |  /upload, /jobs/...  |
          +----------+-----------+
                     |
                     | DB session (SQLAlchemy)
                     v
         +-----------+------------+
         |    Services Layer      |
         |  PDF / Job / Email     |
         +-----------+------------+
                     |
      +--------------+------------------+
      |                                 |
      |                                 v
      |                       +---------+---------+
      |                       |    Celery Worker  |
      |  enqueue job          |  process_pdf_job  |
      +---------------------->+---------+---------+
                                      |
                                      | CrewOrchestrator
                                      v
        +-------------------- Multi-Agent Crew --------------------+
        |  PDF Analyzer   ->   Email Composer   ->  Email Validator|
        +--------------------+-----------------+-------------------+
                                      |
                                      v
                         +------------+-----------+
                         |     Email Service      |
                         |  SMTP / SendGrid API  |
                         +------------+----------+
                                      |
                                      v
                              External Email System

```

### Folder Structure

```text
backend/
 ├── app/
 │   ├── api/
 │   │   └── routes.py
 │   ├── core/
 │   │   ├── config.py
 │   │   └── logging.py
 │   ├── agents/
 │   │   ├── pdf_analyzer.py
 │   │   ├── email_composer.py
 │   │   ├── email_sender.py
 │   │   └── crew_orchestrator.py
 │   ├── services/
 │   │   ├── pdf_service.py
 │   │   ├── email_service.py
 │   │   └── job_service.py
 │   ├── workers/
 │   │   └── celery_worker.py
 │   ├── models/
 │   │   ├── user.py
 │   │   ├── document.py
 │   │   ├── job.py
 │   │   ├── agent_output.py
 │   │   ├── email_record.py
 │   │   └── execution_log.py
 │   ├── repositories/
 │   │   └── base_repository.py
 │   ├── database/
 │   │   ├── session.py
 │   │   └── base.py
 │   └── utils/
│       ├── pdf_parser.py
│       ├── email_templates.py
│       └── retry.py
├── tests/
│   └── sample.pdf
├── main.py
├── requirements.txt
└── README.md
```

### Agent Orchestration Workflow

1. **PDF Upload**
   - Client calls `POST /api/upload` with a multi-page PDF and `recipient_email` query parameter.
   - `PDFService` validates file type and size, detects invalid/corrupted PDFs, persists document metadata, and extracts text/structure.
   - `JobService` creates a `ProcessingJob` with status `PENDING`.
   - A Celery task (`process_pdf_job`) is enqueued with the job ID and recipient email.

2. **Crew Execution (in Celery Worker)**
   - Job state is atomically updated to `PROCESSING` with the Celery task ID.
   - `CrewOrchestrator` is instantiated with the job and document text.
   - **PDF Analyzer Agent**:
     - Uses an LLM (via LangChain) to generate deterministic JSON of headings, sections, entities, and tables.
     - Result is saved to `AgentOutput` and `ExecutionLog`.
   - **Email Composer Agent**:
     - Consumes analyzer output and returns JSON `{ subject, body }`.
     - Output stored in `AgentOutput`.
   - **Email Delivery Validator Agent**:
     - Lightly refines subject/body, ensuring professionalism.
     - Final JSON stored as `AgentOutput`.
   - **EmailService**:
     - Sends email via SMTP or SendGrid.
     - Writes an `EmailRecord` with status, provider metadata, and timestamps.
   - On success, job is marked `COMPLETED`; on failure, `FAILED` with error message and retries handled by Celery.

### Concurrency & Queue Strategy

- **Redis** is used as the Celery broker and result backend.
- **Celery Worker**:
  - `process_pdf_job` runs with `acks_late` and `worker_prefetch_multiplier=1` to avoid lost work and support fair scheduling.
  - `autoretry_for` with exponential backoff handles transient failures (LLM timeouts, SMTP hiccups, network blips).
- **Job States**:
  - `PENDING`: Job created, not yet picked by worker.
  - `PROCESSING`: Task is executing in a worker; Celery task ID persisted.
  - `COMPLETED`: All agents ran successfully and email was sent (or at least attempted and recorded).
  - `FAILED`: Final failure after retries; error message stored.
- **Atomicity & Idempotency**:
  - SQLAlchemy sessions are transactionally committed in FastAPI and Celery workers.
  - Before processing, the worker checks if the job is already `COMPLETED` to avoid duplicate work.

### Database Design

- **User**
  - `id`, `email` (unique), `full_name`, timestamps.
- **Document**
  - Links to optional `user_id`.
  - Stores filename, content type, file size, storage path, extracted text, and structured JSON.
  - Indexed by `user_id` and `created_at` for efficient listing.
- **ProcessingJob**
  - Links to `document_id` and optional `user_id`.
  - `status` (PENDING / PROCESSING / COMPLETED / FAILED).
  - `celery_task_id` for tracking in the queue.
  - Error message and arbitrary metadata.
- **AgentOutput**
  - Links to `job_id`.
  - `agent_name`, `step`, raw LLM text, and deterministic structured JSON output.
- **EmailRecord**
  - Links to `job_id`.
  - Recipient, subject, body, provider, status, and provider response metadata.
- **ExecutionLog**
  - Free-form execution events for observability, indexed by `job_id` and timestamp.

All tables include `created_at` and many have `updated_at` plus indexes on key foreign keys and status fields to support queries at scale.

### Error Handling Approach

- **LLM Timeouts / Agent Failures**
  - LangChain LLM client is configured with a timeout.
  - Celery task wraps the full orchestration; failures bubble up and trigger automatic retries with backoff.
  - If an agent output is missing or malformed, deterministic fallback JSON or email templates are used.
- **SMTP / SendGrid Errors**
  - Exceptions are captured, logged, and stored in `EmailRecord.response_metadata` with status `FAILED`.
  - They can cause Celery retries if configured that way or be surfaced via job status queries.
- **Invalid PDFs**
  - Detected at upload time via parsing; return `400` from `POST /upload` with a safe error message.
- **Database Disconnects**
  - SQLAlchemy uses `pool_pre_ping` and transactions are rolled back on exception.
- **Unexpected Outputs**
  - Agents are instructed to output JSON; code defensively checks for keys and falls back to deterministic templates.
- **API Responses**
  - FastAPI endpoints do not expose raw tracebacks; they return structured error messages with appropriate HTTP codes.

### Observability & Metrics

- **Structured Logging**
  - Loguru configured to emit JSON to stdout.
  - `log_execution_event` helper standardizes event logging.
- **Request / Job Tracing**
  - `ExecutionLog` table stores job-level execution events (crew start/end, per-agent steps, email delivery).
  - Logs include `job_id` and high-level event names.
- **Metrics Hooks**
  - The design is ready to integrate Prometheus or other metrics providers by instrumenting FastAPI and Celery.

### API Endpoints

- `POST /api/upload`
  - Query: `recipient_email`
  - Body: `multipart/form-data` with `file` (PDF).
  - Returns: `{ "job_id": int, "status": "PENDING" | "PROCESSING" }`
- `GET /api/jobs/{id}`
  - Returns job status, associated document, error message, and timestamps.
- `GET /api/documents`
  - Lists documents with basic metadata and pagination (`skip`, `limit`).
- `GET /api/emails`
  - Lists sent/failed/pending emails with minimal metadata.
- `GET /api/health`
  - API health check (in addition to root `/health` from `main.py`).

### Scaling Strategy & 10x Load Behavior

- **Horizontal Scale**
  - Multiple API replicas behind a load balancer (stateless FastAPI).
  - Multiple Celery workers across nodes connected to the same Redis and Postgres.
- **Database**
  - Use connection pooling, proper indexes, and possibly read replicas at higher scale.
  - Partition or archive old `ExecutionLog` and `AgentOutput` tables if they grow large.
- **Workers**
  - Increase worker concurrency and number of pods/instances to handle more PDFs in parallel.
- **LLM Calls**
  - Control concurrency and rate limiting to avoid provider throttling.
  - Cache stable parts of analysis if multiple downstream actions depend on the same content.

At 10x load, bottlenecks will likely appear in:

- LLM rate limits and latency.
- Email provider rate limits.
- Postgres connection pool and write throughput (especially on `ExecutionLog`).

Mitigations:

- Add queues or backpressure for LLM and email operations.
- Batch logging or move to more write-optimized storage for logs (e.g., log aggregation stack).
- Increase Postgres resources and use connection poolers (PgBouncer).

### Setup Instructions

1. **Clone & Enter Project**

```bash
cd backend
cp .env.example .env
```

2. **Configure Environment**

- Update `.env` with your Postgres, Redis, email backend, and `OPENAI_API_KEY`.

3. **Install Dependencies (Local Dev)**

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install --upgrade pip
pip install -r requirements.txt
```

4. **Run Database**

Start Postgres and Redis using your preferred method (local installation, your own container stack, or managed cloud services). Ensure the connection details match your `.env` configuration.

5. **Run Migrations**

You can initialize Alembic and generate migrations from the SQLAlchemy models (not fully scripted here), or create the tables directly in development using SQLAlchemy metadata.

6. **Run API**

```bash
uvicorn main:app --reload
```

7. **Run Celery Worker**

```bash
celery -A app.workers.celery_worker.celery_app worker --loglevel=INFO
```

### Testing

- **Full suite (config, DB, Redis, API server, HTTP)**  
  From `backend/` with dependencies installed:
  ```bash
  python run_all_tests.py
  ```
  This checks settings load, DB and Redis connectivity, starts the API server, and runs health + upload + job-status + error-path checks. For managed Redis (e.g. Redis Labs), set `REDIS_URL` with auth, e.g. `redis://default:YOUR_PASSWORD@host:port/0`.

- **HTTP-only (no app import)**  
  With the API already running (e.g. `uvicorn main:app --reload`):
  ```bash
  python test_http_only.py
  ```
  Optional: `TEST_BASE_URL=http://localhost:8000 python test_http_only.py`.

**Why POST /upload might timeout**

- **Sync work in the request** – Upload does blocking I/O: read file, write to disk, parse PDF, DB writes, Celery enqueue. The route is implemented as a sync endpoint (`def`) so FastAPI runs it in a thread pool and does not block the event loop; if the pool is busy or one step is very slow, the client can still hit a read timeout.
- **Database latency** – Remote Postgres (e.g. Aiven) adds round-trips for each `flush`; SSL and cold connections can make the first request slower.
- **Redis/Celery** – `process_pdf_job.delay()` sends a message to Redis; high latency or connection issues to Redis Labs can delay the response.
- **Disk I/O** – Writing under `storage/documents` can be slow on a synced or network drive.
- **PDF parsing** – `extract_pdf_content` can be slow for large or complex PDFs.

If timeouts persist, run the API with logging (e.g. `uvicorn main:app --log-level debug`) and watch where the request stalls.

### Bonus Features

- **Parallel Tool Calls**
  - CrewAI can be extended to add parallel tools for table extraction, entity resolution, or external system lookups; the orchestrator is designed around a clear sequence but can be adapted to `Process.hierarchical` or `Process.parallel`.
- **Streaming Agent Reasoning**
  - LLM clients can be configured for streaming tokens and thought traces; currently, the system logs step boundaries, but can be extended to log incremental reasoning.
- **Dead Letter Queue**
  - Failed jobs after max retries are marked `FAILED` in the DB, effectively forming a dead letter set that can be re-queued or inspected via custom admin APIs or scripts.

