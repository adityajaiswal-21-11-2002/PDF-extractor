"""
Quick test of email sending (SendGrid or SMTP).
Run: python test_email.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def main():
    from app.core.config import settings
    from app.services.email_service import EmailService

    backend = settings.EMAIL_BACKEND.lower()
    print(f"Testing email backend: {backend}")

    svc = EmailService()
    to_address = "test@example.com"  # change to your email to receive
    subject = "PDF Extractor - Test Email"
    body = "This is a test email from the AI Agent Orchestration backend. If you received this, email sending works."

    if backend == "sendgrid":
        if not settings.SENDGRID_API_KEY:
            print("FAIL: SENDGRID_API_KEY not set in .env")
            return 1
        try:
            metadata = svc._send_sendgrid(to_address, subject, body)
            print(f"PASS: SendGrid sent successfully. {metadata}")
            return 0
        except Exception as e:
            print(f"FAIL: SendGrid error: {e}")
            return 1
    else:
        print(f"Testing SMTP ({settings.SMTP_HOST}:{settings.SMTP_PORT})...")
        try:
            metadata = svc._send_smtp(to_address, subject, body)
            print(f"PASS: SMTP sent successfully. {metadata}")
            return 0
        except Exception as e:
            print(f"FAIL: SMTP error: {e}")
            return 1

if __name__ == "__main__":
    sys.exit(main())
