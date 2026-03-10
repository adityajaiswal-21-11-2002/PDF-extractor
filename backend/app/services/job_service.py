from typing import Any, Dict

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.job import JobStatusEnum, ProcessingJob


logger = get_logger(__name__)


class JobService:
    """
    Service for creating and updating processing jobs with atomic state transitions.
    """

    def create_job(
        self,
        db: Session,
        document_id: int,
        user_id: int | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> ProcessingJob:
        job = ProcessingJob(
            document_id=document_id,
            user_id=user_id,
            status=JobStatusEnum.PENDING,
            job_metadata=metadata or {},
        )
        db.add(job)
        db.flush()
        logger.info({"event": "job_created", "job_id": job.id})
        return job

    def mark_processing(self, db: Session, job: ProcessingJob, celery_task_id: str) -> None:
        if job.status not in (JobStatusEnum.PENDING, JobStatusEnum.FAILED):
            return
        job.status = JobStatusEnum.PROCESSING
        job.celery_task_id = celery_task_id
        db.add(job)
        db.flush()
        logger.info({"event": "job_mark_processing", "job_id": job.id})

    def mark_completed(self, db: Session, job: ProcessingJob) -> None:
        job.status = JobStatusEnum.COMPLETED
        db.add(job)
        db.flush()
        logger.info({"event": "job_completed", "job_id": job.id})

    def mark_failed(self, db: Session, job: ProcessingJob, error_message: str) -> None:
        job.status = JobStatusEnum.FAILED
        job.error_message = error_message[:2000]
        db.add(job)
        db.flush()
        logger.error(
            {
                "event": "job_failed",
                "job_id": job.id,
                "error_message": job.error_message,
            }
        )

