import os

import app.pkg_resources_shim  # noqa: F401 - bootstrap before crewai
from celery import Celery
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import db_session
from app.models.job import JobStatusEnum, ProcessingJob
from app.services.job_service import JobService
from app.agents.crew_orchestrator import CrewOrchestrator


celery_app = Celery(
    "agent_orchestrator",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.task_routes = {
    "app.workers.celery_worker.process_pdf_job": {"queue": "jobs"},
}

celery_app.conf.task_default_queue = "jobs"
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.task_acks_late = True
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.broker_heartbeat = 10
celery_app.conf.broker_connection_retry_on_startup = True

# Dead letter queue (bonus)
celery_app.conf.task_queues = (
    # main queue is implicit
)

logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def process_pdf_job(self, job_id: int, recipient_email: str) -> None:
    """
    Celery task that orchestrates the full CrewAI workflow for a given job.
    """
    logger.info("Starting processing for job_id=%s", job_id)

    with db_session() as db:  # type: Session
        job_service = JobService()
        job: ProcessingJob | None = db.query(ProcessingJob).get(job_id)
        if not job:
            logger.error("Job not found: %s", job_id)
            return

        # Duplicate processing prevention
        if job.status == JobStatusEnum.COMPLETED:
            logger.info("Job already completed: %s", job_id)
            return

        job_service.mark_processing(db, job, celery_task_id=self.request.id)

        document = job.document
        if not document or not document.extracted_text:
            job_service.mark_failed(db, job, "Document or extracted text missing.")
            return

        try:
            orchestrator = CrewOrchestrator(
                db=db,
                job=job,
                document_text=document.extracted_text,
            )
            orchestrator.run(recipient_email=recipient_email)
            job_service.mark_completed(db, job)
        except Exception as exc:
            logger.exception("Error processing job %s: %s", job_id, exc)
            job_service.mark_failed(db, job, str(exc))
            raise

