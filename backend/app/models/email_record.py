from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database.base import Base


class EmailStatusEnum(str):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class EmailRecord(Base):
    __tablename__ = "email_records"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("processing_jobs.id"), nullable=False, index=True)
    to_address = Column(String(255), nullable=False, index=True)
    subject = Column(String(512), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default=EmailStatusEnum.PENDING)
    provider = Column(String(32), nullable=False)
    provider_message_id = Column(String(255), nullable=True)
    response_metadata = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    job = relationship("ProcessingJob", backref="emails")


Index(
    "ix_email_records_status_created",
    EmailRecord.status,
    EmailRecord.created_at.desc(),
)

