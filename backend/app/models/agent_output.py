from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database.base import Base


class AgentOutput(Base):
    __tablename__ = "agent_outputs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("processing_jobs.id"), nullable=False, index=True)
    agent_name = Column(String(128), nullable=False, index=True)
    step = Column(String(128), nullable=False)
    raw_output = Column(Text, nullable=True)
    structured_output = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )

    job = relationship("ProcessingJob", backref="agent_outputs")


Index(
    "ix_agent_outputs_job_step",
    AgentOutput.job_id,
    AgentOutput.step,
    AgentOutput.created_at.desc(),
)

