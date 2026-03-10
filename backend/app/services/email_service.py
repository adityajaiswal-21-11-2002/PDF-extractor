from typing import Any, Dict, Optional

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.email_record import EmailRecord, EmailStatusEnum
from app.utils.email_templates import default_email_subject


logger = get_logger(__name__)


class EmailService:
    """
    Service responsible for sending emails via SMTP or SendGrid and persisting metadata.
    """

    def __init__(self) -> None:
        self.backend = settings.EMAIL_BACKEND.lower()

    def _send_smtp(
        self, to_address: str, subject: str, body: str
    ) -> Dict[str, Any]:
        msg = MIMEMultipart()
        msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            response = server.sendmail(settings.EMAIL_FROM, [to_address], msg.as_string())
            server.quit()
            return {"response": str(response)}
        except Exception as e:
            logger.error({"event": "smtp_send_error", "error": str(e)})
            raise

    def _send_sendgrid(
        self, to_address: str, subject: str, body: str
    ) -> Dict[str, Any]:
        if not settings.SENDGRID_API_KEY:
            raise RuntimeError("SENDGRID_API_KEY is not configured.")

        url = "https://api.sendgrid.com/v3/mail/send"
        payload = {
            "personalizations": [{"to": [{"email": to_address}]}],
            "from": {"email": settings.EMAIL_FROM, "name": settings.EMAIL_FROM_NAME},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}],
        }
        headers = {
            "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
            "Content-Type": "application/json",
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        if not resp.ok:
            logger.error(
                {
                    "event": "sendgrid_send_error",
                    "status_code": resp.status_code,
                    "body": resp.text,
                }
            )
            resp.raise_for_status()
        return {"status_code": resp.status_code, "body": resp.text}

    def send_email(
        self,
        db: Session,
        job_id: int,
        to_address: str,
        subject: Optional[str],
        body: str,
    ) -> EmailRecord:
        subject = subject or default_email_subject()

        email_record = EmailRecord(
            job_id=job_id,
            to_address=to_address,
            subject=subject,
            body=body,
            status=EmailStatusEnum.PENDING,
            provider=self.backend,
        )
        db.add(email_record)
        db.flush()

        try:
            if self.backend == "sendgrid":
                metadata = self._send_sendgrid(to_address, subject, body)
            else:
                metadata = self._send_smtp(to_address, subject, body)

            email_record.status = EmailStatusEnum.SENT
            email_record.response_metadata = metadata
        except Exception as e:
            logger.error(
                {
                    "event": "email_send_error",
                    "backend": self.backend,
                    "to": to_address,
                    "error": str(e),
                }
            )
            email_record.status = EmailStatusEnum.FAILED
            email_record.response_metadata = {"error": str(e)}

        db.add(email_record)
        db.flush()
        return email_record

