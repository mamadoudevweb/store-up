"""Production configuration — all secrets must come from environment variables."""
from __future__ import annotations

from pydantic import field_validator

from .base import BaseConfig


class ProductionConfig(BaseConfig):
    FLASK_ENV: str = "production"
    DEBUG: bool = False
    TESTING: bool = False

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_set(cls, v: str) -> str:
        if v == "dev-secret-key-change-in-prod":
            raise ValueError("SECRET_KEY must be explicitly set in production environment")
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def database_url_must_be_postgres(cls, v: str) -> str:
        if not v.startswith("postgresql"):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL in production")
        return v

    @field_validator("SUPERUSER_PASSWORD")
    @classmethod
    def superuser_password_must_be_set(cls, v: str) -> str:
        if v in {"change-me-immediately", ""}:
            raise ValueError("SUPERUSER_PASSWORD must be explicitly set in production")
        return v
