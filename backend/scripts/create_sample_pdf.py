#!/usr/bin/env python3
"""Create a valid sample PDF with extractable text for testing."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO


def main():
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica", 14)

    # Page 1
    c.drawString(100, 750, "Sample Document for AI Agent Orchestrator")
    c.drawString(100, 720, "This is a test PDF with extractable text for CrewAI analysis.")
    c.drawString(100, 680, "Project Summary:")
    c.drawString(120, 650, "- Q1 2025 revenue increased by 15% year-over-year.")
    c.drawString(120, 620, "- Customer satisfaction score: 4.2/5.0")
    c.drawString(120, 590, "- Key milestones: API v2 launch, mobile app beta")
    c.drawString(100, 550, "Next Steps:")
    c.drawString(120, 520, "- Schedule review meeting for Q2 planning")
    c.drawString(120, 490, "- Contact: team@example.com")
    c.drawString(120, 460, "- Deadline: March 15, 2025")

    # Page 2
    c.showPage()
    c.setFont("Helvetica", 14)
    c.drawString(100, 750, "Additional Notes")
    c.drawString(100, 700, "This document demonstrates PDF text extraction for the")
    c.drawString(100, 670, "multi-agent workflow: PDF Analyzer -> Email Composer -> Email Sender.")
    c.drawString(100, 620, "Entities: John Smith (CEO), Acme Corp, 2025-03-15")

    c.save()
    buf.seek(0)

    out_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "tests", "sample.pdf"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(buf.getvalue())
    print(f"Created {out_path}")


if __name__ == "__main__":
    main()
