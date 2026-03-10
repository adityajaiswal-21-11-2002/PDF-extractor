from typing import Any, Dict

from pypdf import PdfReader


def extract_pdf_content(file_path: str) -> Dict[str, Any]:
    """
    Basic PDF text and structure extraction.
    In production you may want to use more advanced tooling (layout analysis, table extraction).
    """
    reader = PdfReader(file_path)
    full_text = ""
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        full_text += f"\n\n=== Page {page_number} ===\n{text}"
        pages.append(
            {
                "page_number": page_number,
                "text": text,
            }
        )

    # Placeholder structure; can be enriched by LLM agents later
    structured = {
        "pages": pages,
        "headings": [],
        "sections": [],
        "tables": [],
    }

    return {"text": full_text.strip(), "structured": structured}

