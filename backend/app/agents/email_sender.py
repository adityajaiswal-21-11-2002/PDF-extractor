from typing import Any, Dict

from crewai import Agent, Task

from app.core.logging import get_logger


logger = get_logger(__name__)


def build_email_sender_agent(llm) -> Agent:
    """
    Agent that validates and finalizes email content prior to delivery.
    """
    return Agent(
        role="Email Delivery Validator",
        goal=(
            "Validate email content for professionalism, clarity, and completeness "
            "before it is sent, and confirm or lightly edit as needed."
        ),
        backstory=(
            "You act as a final reviewer ensuring emails are ready to send to executives or clients."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


def email_sender_task(agent: Agent, context_task=None) -> Task:
    """
    Task that ensures the email is properly formatted and safe to send.
    """
    description = (
        "You are given a JSON object representing an email with 'subject' and 'body'. "
        "Lightly refine if necessary, ensuring it is professional and safe. "
        "Return JSON with the same keys: 'subject' and 'body'. "
        "Do not add disclaimers unless absolutely required. "
        "Only output valid JSON."
    )

    task_kw = dict(
        description=description,
        agent=agent,
        expected_output="A JSON object with 'subject' and 'body' keys.",
        async_execution=False,
        output_json=True,
    )
    if context_task is not None:
        task_kw["context"] = [context_task]
    return Task(**task_kw)

