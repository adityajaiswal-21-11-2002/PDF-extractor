from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger


logger = get_logger(__name__)


def init_error_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers for the FastAPI application.
    """

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.error(
            {
                "event": "request_validation_error",
                "path": str(request.url),
                "errors": exc.errors(),
            }
        )
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation error.",
                "errors": exc.errors(),
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        logger.error(
            {
                "event": "http_exception",
                "path": str(request.url),
                "status_code": exc.status_code,
                "detail": exc.detail,
            }
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            {
                "event": "unhandled_exception",
                "path": str(request.url),
                "error": str(exc),
            }
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error."},
        )

