from typing import Dict


def default_email_subject() -> str:
    return "Contextual Summary and Next Steps"


def render_email_body(context: Dict) -> str:
    """
    Fallback deterministic email body in case LLM composition fails.
    """
    doc_title = context.get("document_title") or "your document"
    summary = context.get("summary") or "We have processed your document."

    return (
        f"Hello,\n\n"
        f"{summary}\n\n"
        f"This message was generated automatically based on {doc_title}.\n\n"
        f"Best regards,\n"
        f"AI Orchestrator"
    )

