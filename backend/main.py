from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import app.models  # noqa: F401 - register all models for SQLAlchemy relationships
from app.api.routes import api_router
from app.core.config import settings
from app.core.error_handlers import init_error_handlers
from app.core.logging import configure_logging


BASE_DIR = Path(__file__).resolve().parent


def create_app() -> FastAPI:
    """
    Application factory for FastAPI app.
    """
    configure_logging()

    # Create DB tables when running locally (e.g. tests, dev) so upload works
    if settings.ENV == "local":
        try:
            from app.database.base import Base
            from app.database.session import engine
            Base.metadata.create_all(bind=engine)
        except Exception as e:
            import sys
            print(f"create_all skipped: {e}", file=sys.stderr)

    app = FastAPI(
        title="AI Agent Orchestration Backend",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Global error handlers
    init_error_handlers(app)

    # CORS configuration (adjust origins for production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include versioned API router
    app.include_router(api_router, prefix="/api")

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        """
        Serve a simple HTML frontend for uploading PDFs.
        """
        return FileResponse(BASE_DIR / "index.html")

    return app


app = create_app()


@app.get("/health", tags=["health"])
async def health_check():
    """
    Lightweight health check for uptime monitoring.
    """
    return {"status": "ok", "version": settings.APP_VERSION}

