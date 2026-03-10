from typing import Any, Dict

from crewai import Agent, Task

from app.core.logging import get_logger


logger = get_logger(__name__)


def build_email_composer_agent(llm) -> Agent:
    """
    Agent that composes professional, contextual emails based on analyzer output.
    """
    return Agent(
        role="Email Composer",
        goal=(
            "Generate concise, professional, and context-aware emails based on "
            "structured analysis of a document."
        ),
        backstory=(
            "You are a senior communications specialist who drafts clear, actionable "
            "emails tailored to the document content and recipient."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


def email_composer_task(agent: Agent, analysis_json: Dict[str, Any]) -> Task:
    """
    Task for generating email subject and body from analysis.
    """
    description = (
        "You are given a structured JSON analysis of a PDF document. "
        "Craft a professional email summarizing the key insights and proposing next steps. "
        "Output JSON with the following keys:\n"
        "- subject: string\n"
        "- body: string (plain text, no markdown)\n\n"
        "Only output valid JSON. Do not include explanations."
    )

    return Task(
        description=description,
        agent=agent,
        inputs={"analysis": analysis_json},
        expected_output="A JSON object with 'subject' and 'body' keys.",
        async_execution=False,
        output_json=True,
    )

