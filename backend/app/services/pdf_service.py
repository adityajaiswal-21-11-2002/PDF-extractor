import os
import uuid
from typing import Any, Dict, Tuple

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.document import Document
from app.utils.pdf_parser import extract_pdf_content


logger = get_logger(__name__)


class PDFService:
    """
    Service responsible for PDF validation, storage, and extraction.
    """

    def __init__(self, storage_dir: str = "storage/documents"):
        self.storage_dir = storage_dir
        try:
            os.makedirs(self.storage_dir, exist_ok=True)
        except OSError as e:
            logger.error(
                {
                    "event": "storage_dir_init_error",
                    "storage_dir": self.storage_dir,
                    "error": str(e),
                }
            )
            raise HTTPException(
                status_code=500,
                detail="File storage is temporarily unavailable.",
            ) from e

    def _save_upload_to_disk(self, file: UploadFile) -> Tuple[str, int]:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")

        # Limit: 20MB (configurable in a real system)
        try:
            contents = file.file.read()
        except Exception as e:
            logger.error(
                {
                    "event": "file_read_error",
                    "filename": file.filename,
                    "error": str(e),
                }
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to read uploaded file.",
            ) from e
        file_size = len(contents)
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        if file_size > 20 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 20MB).")

        unique_name = f"{uuid.uuid4()}.pdf"
        storage_path = os.path.join(self.storage_dir, unique_name)
        try:
            with open(storage_path, "wb") as f:
                f.write(contents)
        except OSError as e:
            logger.error(
                {
                    "event": "pdf_write_error",
                    "storage_path": storage_path,
                    "error": str(e),
                }
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to store uploaded file.",
            ) from e

        return storage_path, file_size

    def create_document_from_upload(
        self,
        db: Session,
        file: UploadFile,
        user_id: int | None = None,
    ) -> Document:
        storage_path, file_size = self._save_upload_to_disk(file)

        try:
            parsed: Dict[str, Any] = extract_pdf_content(storage_path)
        except Exception as e:
            logger.error({"event": "pdf_parse_error", "error": str(e)})
            # Mark file as corrupted or unreadable
            raise HTTPException(status_code=400, detail="Invalid or corrupted PDF.")

        doc = Document(
            user_id=user_id,
            filename=file.filename,
            content_type=file.content_type or "application/pdf",
            file_size=file_size,
            storage_path=storage_path,
            extracted_text=parsed.get("text"),
            extracted_structure=parsed.get("structured"),
        )
        db.add(doc)
        db.flush()
        return doc

