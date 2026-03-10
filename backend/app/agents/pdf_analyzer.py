from typing import Any, Dict

from crewai import Agent, Task, Crew, Process

from app.core.logging import get_logger


logger = get_logger(__name__)


def build_pdf_analyzer_agent(llm) -> Agent:
    """
    Agent that analyzes PDF text and extracts structured entities.
    """
    return Agent(
        role="PDF Analyzer",
        goal=(
            "Analyze the provided PDF text and extract a deterministic, well-structured "
            "JSON object with headings, sections, key entities, and any tabular data."
        ),
        backstory=(
            "You are an expert document analyst who converts unstructured PDFs "
            "into clean JSON suitable for downstream automation."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


def pdf_analyzer_task(agent: Agent, pdf_text: str) -> Task:
    """
    Task for PDF analysis, enforcing deterministic JSON output.
    """
    description = (
        "Given the full text of a PDF document, extract a structured JSON object with the following keys:\n"
        "- headings: array of strings\n"
        "- sections: array of objects with 'title' and 'content'\n"
        "- entities: object with keys like 'people', 'organizations', 'dates', each an array of strings\n"
        "- tables: array of objects describing any tabular content\n\n"
        "Only output valid JSON. Do not include any explanatory text."
    )

    return Task(
        description=description,
        agent=agent,
        inputs={"pdf_text": pdf_text},
        expected_output="A single JSON object with the schema described above.",
        async_execution=False,
        output_json=True,
    )

