from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi import status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.database.session import get_db
from app.models.document import Document
from app.models.email_record import EmailRecord
from app.models.job import JobStatusEnum, ProcessingJob
from app.services.job_service import JobService
from app.services.pdf_service import PDFService
from app.workers.celery_worker import process_pdf_job


logger = get_logger(__name__)

api_router = APIRouter()


@api_router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
def upload_pdf(
    recipient_email: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF, create a processing job, and enqueue Celery task.
    Implemented as sync (def) so FastAPI runs it in a thread pool; avoids blocking
    the event loop on slow DB/disk/Celery I/O and prevents upload timeouts.
    """
    pdf_service = PDFService()
    job_service = JobService()

    try:
        document = pdf_service.create_document_from_upload(
            db, file=file, user_id=None
        )
        job = job_service.create_job(
            db=db,
            document_id=document.id,
            user_id=None,
            metadata={"recipient_email": recipient_email},
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            {
                "event": "upload_init_error",
                "recipient_email": recipient_email,
                "error": str(exc),
            }
        )
        detail = "Failed to create processing job."
        if settings.ENV == "local":
            detail += f" ({type(exc).__name__}: {exc})"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        ) from exc

    try:
        celery_result = process_pdf_job.delay(job.id, recipient_email)
        job_service.mark_processing(db, job, celery_task_id=celery_result.id)
    except Exception as exc:
        logger.error(
            {
                "event": "enqueue_job_error",
                "job_id": job.id,
                "error": str(exc),
            }
        )
        job_service.mark_failed(
            db, job, "Background processing is temporarily unavailable."
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Background processing is temporarily unavailable. "
                "Please try again later."
            ),
        ) from exc

    return {"job_id": job.id, "status": job.status}


@api_router.get("/jobs/{job_id}", response_model=dict)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(ProcessingJob).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    public_error: str | None = None
    if job.status == JobStatusEnum.FAILED:
        public_error = "Job failed during processing. Please try again later."

    return {
        "id": job.id,
        "status": job.status,
        "document_id": job.document_id,
        "error_message": public_error,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


@api_router.get("/documents", response_model=List[dict])
async def list_documents(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    docs = (
        db.query(Document)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "file_size": d.file_size,
            "created_at": d.created_at,
        }
        for d in docs
    ]


@api_router.get("/emails", response_model=List[dict])
async def list_emails(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    emails = (
        db.query(EmailRecord)
        .order_by(EmailRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": e.id,
            "job_id": e.job_id,
            "to": e.to_address,
            "subject": e.subject,
            "status": e.status,
            "provider": e.provider,
            "created_at": e.created_at,
        }
        for e in emails
    ]


@api_router.get("/health", tags=["health"])
async def api_health():
    """
    Lightweight API-level health check.
    """
    return {"status": "ok", "version": settings.APP_VERSION}

