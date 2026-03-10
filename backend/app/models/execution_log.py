from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database.base import Base


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("processing_jobs.id"), nullable=True, index=True)
    agent_name = Column(String(128), nullable=True, index=True)
    level = Column(String(32), nullable=False, default="INFO")
    event = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    log_metadata = Column("metadata", JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )

    job = relationship("ProcessingJob", backref="execution_logs")


Index(
    "ix_execution_logs_job_created",
    ExecutionLog.job_id,
    ExecutionLog.created_at.desc(),
)

