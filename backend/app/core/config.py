from functools import lru_cache
from typing import List, Optional, Union
from urllib.parse import quote_plus

from pydantic import EmailStr, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _build_postgres_uri(
    user: str,
    password: str,
    host: str,
    port: int,
    db: str,
) -> str:
    user_enc = quote_plus(user)
    pass_enc = quote_plus(password)
    return f"postgresql+psycopg2://{user_enc}:{pass_enc}@{host}:{port}/{db}"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    APP_NAME: str = "AI Agent Orchestration Backend"
    APP_VERSION: str = "0.1.0"
    ENV: str = Field("local", description="Environment name: local/staging/prod")

    API_V1_PREFIX: str = "/api"

    # Render provides DATABASE_URL; otherwise use POSTGRES_* vars
    DATABASE_URL: Optional[str] = None
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "agent_orchestrator"
    SQLALCHEMY_ECHO: bool = False

    # Render provides REDIS_URL when Redis is connected
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    EMAIL_FROM: EmailStr = "no-reply@example.com"
    EMAIL_FROM_NAME: str = "AI Orchestrator"
    EMAIL_BACKEND: str = Field("smtp", description="Email backend: smtp or sendgrid")

    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True

    SENDGRID_API_KEY: Optional[str] = None
    SECRET_KEY: str = "CHANGE_ME"
    OPENAI_API_KEY: Optional[str] = None
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = []

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            # Render / Railway provide DATABASE_URL; ensure psycopg2 scheme
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = "postgresql+psycopg2://" + url[11:]
            elif url.startswith("postgresql://") and "psycopg2" not in url:
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return url
        return _build_postgres_uri(
            self.POSTGRES_USER,
            self.POSTGRES_PASSWORD,
            self.POSTGRES_SERVER,
            self.POSTGRES_PORT,
            self.POSTGRES_DB,
        )

    @model_validator(mode="after")
    def _default_celery_from_redis(self):
        if self.CELERY_BROKER_URL is None:
            object.__setattr__(self, "CELERY_BROKER_URL", self.REDIS_URL)
        if self.CELERY_RESULT_BACKEND is None:
            object.__setattr__(self, "CELERY_RESULT_BACKEND", self.REDIS_URL)
        return self

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, list):
            return v
        return []

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
