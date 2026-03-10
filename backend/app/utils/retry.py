import time
from typing import Any, Callable, Type


def exponential_backoff_retry(
    func: Callable,
    exceptions: tuple[Type[BaseException], ...],
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 10.0,
) -> Any:
    """
    Simple exponential backoff wrapper for retrying functions.
    Intended for non-async contexts such as Celery tasks.
    """
    attempt = 0
    while True:
        try:
            return func()
        except exceptions:  # type: ignore[misc]
            attempt += 1
            if attempt > max_retries:
                raise
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            time.sleep(delay)

