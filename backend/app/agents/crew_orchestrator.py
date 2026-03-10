import json
from typing import Any, Dict, Tuple

from crewai import Crew, Process
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger, log_execution_event
from app.models.agent_output import AgentOutput
from app.models.job import ProcessingJob
from app.models.execution_log import ExecutionLog
from app.services.email_service import EmailService
from app.utils.email_templates import render_email_body
from .pdf_analyzer import build_pdf_analyzer_agent, pdf_analyzer_task
from .email_composer import build_email_composer_agent, email_composer_task
from .email_sender import build_email_sender_agent, email_sender_task


logger = get_logger(__name__)


def _parse_json_output(raw: Any) -> Dict | None:
    """Parse JSON from task output (string or dict)."""
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    if hasattr(raw, "output_json") and raw.output_json is not None:
        return raw.output_json
    s = str(raw).strip()
    if not s:
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


class CrewOrchestrator:
    """
    Orchestrates the multi-agent workflow:
    PDF Analyzer -> Email Composer -> Email Sender -> EmailService.
    Uses crew.kickoff() with context for task chaining (crewai 0.11+).
    """

    def __init__(self, db: Session, job: ProcessingJob, document_text: str):
        self.db = db
        self.job = job
        self.document_text = document_text
        self.email_service = EmailService()

        # Configure LLM (can be swapped via settings)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            timeout=30,
        )

    def _persist_agent_output(
        self, agent_name: str, step: str, raw: str | None, structured: Dict | None
    ) -> None:
        out = AgentOutput(
            job_id=self.job.id,
            agent_name=agent_name,
            step=step,
            raw_output=raw,
            structured_output=structured,
        )
        self.db.add(out)
        self.db.flush()

    def _log_step(self, event: str, metadata: Dict[str, Any] | None = None) -> None:
        log_execution_event(
            logger,
            event,
            {"job_id": self.job.id, **(metadata or {})},
        )
        exec_log = ExecutionLog(
            job_id=self.job.id,
            agent_name=None,
            level="INFO",
            event=event,
            log_metadata=metadata or {},
        )
        self.db.add(exec_log)
        self.db.flush()

    def run(self, recipient_email: str) -> Tuple[str, str]:
        """
        Execute the full crew workflow and send the resulting email.
        Returns subject and body used for delivery.
        """
        self._log_step("crew_start")

        # Build agents
        analyzer_agent = build_pdf_analyzer_agent(self.llm)
        composer_agent = build_email_composer_agent(self.llm)
        sender_agent = build_email_sender_agent(self.llm)

        # Tasks with context chaining (crewai 0.11+)
        analyzer_task = pdf_analyzer_task(analyzer_agent, self.document_text)
        composer_task = email_composer_task(composer_agent, context_task=analyzer_task)
        sender_task = email_sender_task(sender_agent, context_task=composer_task)

        crew = Crew(
            agents=[analyzer_agent, composer_agent, sender_agent],
            tasks=[analyzer_task, composer_task, sender_task],
            process=Process.sequential,
            verbose=False,
        )

        self._log_step("pdf_analyzer_start")
        crew.kickoff()
        self._log_step("pdf_analyzer_end")

        # Get outputs from each task (crewai 0.11+)
        analysis_json = _parse_json_output(getattr(analyzer_task, "output", None))
        if not analysis_json:
            analysis_json = {"headings": [], "sections": [], "entities": {}, "tables": []}
        self._persist_agent_output(
            "PDF Analyzer", "analysis", str(getattr(analyzer_task, "output", "")), analysis_json
        )

        self._log_step("email_composer_start")
        email_json = _parse_json_output(getattr(composer_task, "output", None))
        if not email_json or "subject" not in email_json or "body" not in email_json:
            email_json = {
                "subject": "Document Summary",
                "body": render_email_body({"summary": "Your document has been processed."}),
            }
        self._persist_agent_output(
            "Email Composer", "compose", str(getattr(composer_task, "output", "")), email_json
        )
        self._log_step("email_composer_end")

        self._log_step("email_sender_start")
        final_email_json = _parse_json_output(getattr(sender_task, "output", None)) or email_json
        self._persist_agent_output(
            "Email Sender", "finalize", str(getattr(sender_task, "output", "")), final_email_json
        )
        self._log_step("email_sender_end")

        subject = final_email_json.get("subject") or "Document Summary"
        body = final_email_json.get("body") or render_email_body(
            {"summary": "Your document has been processed."}
        )

        self._log_step("email_delivery_start", {"to": recipient_email})
        self.email_service.send_email(
            db=self.db,
            job_id=self.job.id,
            to_address=recipient_email,
            subject=subject,
            body=body,
        )
        self._log_step("email_delivery_end", {"to": recipient_email})

        self._log_step("crew_end")
        return subject, body

