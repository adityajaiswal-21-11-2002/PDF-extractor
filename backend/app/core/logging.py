import logging
import sys
import uuid
from typing import Any, Dict

from loguru import logger


class RequestIdFilter(logging.Filter):
    """
    Logging filter that injects a request_id if not present.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = str(uuid.uuid4())
        return True


def configure_logging() -> None:
    """
    Configure structured logging for the application using loguru.
    """
    logging.basicConfig(level=logging.INFO)

    # On Windows, ensure stdout/stderr use UTF-8 so Unicode in logs doesn't raise
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    # Remove default handlers to avoid duplicate logs
    logger.remove()

    logger.add(
        sys.stdout,
        level="INFO",
        backtrace=False,
        diagnose=False,
        serialize=True,  # structured JSON logs
    )


def get_logger(name: str) -> Any:
    """
    Get a child logger with contextual name.
    """
    return logger.bind(logger_name=name)


def log_execution_event(
    logger_instance: Any,
    event: str,
    extra: Dict[str, Any] | None = None,
) -> None:
    """
    Helper for consistent structured execution logging.
    """
    extra = extra or {}
    logger_instance.info({"event": event, **extra})

