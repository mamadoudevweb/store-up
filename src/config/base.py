"""Base configuration — all environments inherit from this."""
from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Flask ──────────────────────────────────────────────────────────────
    FLASK_ENV: str = "development"
    SECRET_KEY: str = "dev-secret-key-change-in-production-needs-to-be-at-least-32-bytes"
    DEBUG: bool = False
    TESTING: bool = False

    # ── Database ───────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./store_up_dev.db"

    # ── Redis ──────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ────────────────────────────────────────────────────────────────
    JWT_ACCESS_TOKEN_EXPIRES: int = 3600       # seconds
    JWT_REFRESH_TOKEN_EXPIRES: int = 604800    # seconds (7 days)
    JWT_ALGORITHM: str = "HS256"
    JWT_TOKEN_LOCATION: list[str] = ["headers"]
    JWT_HEADER_NAME: str = "Authorization"
    JWT_HEADER_TYPE: str = "Bearer"

    # ── Rate Limiting ──────────────────────────────────────────────────────
    RATE_LIMIT: str = "200 per hour"
    RATE_LIMIT_STORAGE_URL: str = "redis://localhost:6379/1"

    # ── CORS / Domain Restriction ──────────────────────────────────────────
    ALLOWED_ORIGINS: str | list[str] = ["http://localhost:3000"]

    # ── File Uploads ───────────────────────────────────────────────────────
    UPLOAD_FOLDER: str = "uploads"
    MAX_CONTENT_LENGTH: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp"}

    # ── Superuser Bootstrap ────────────────────────────────────────────────
    SUPERUSER_USERNAME: str = "admin"
    SUPERUSER_EMAIL: str = "admin@example.com"
    SUPERUSER_PASSWORD: str = "change-me-immediately"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list[str]) -> str | list[str]:
        if isinstance(v, str):
            if "," in v:
                return [o.strip() for o in v.split(",")]
        return v

    def to_flask_config(self) -> dict[str, object]:
        """Convert to a flat dict compatible with Flask app.config.from_mapping()."""
        return {
            "SECRET_KEY": self.SECRET_KEY,
            "DEBUG": self.DEBUG,
            "TESTING": self.TESTING,
            "SQLALCHEMY_DATABASE_URI": self.DATABASE_URL,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "JWT_SECRET_KEY": self.SECRET_KEY,
            "JWT_ACCESS_TOKEN_EXPIRES": self.JWT_ACCESS_TOKEN_EXPIRES,
            "JWT_REFRESH_TOKEN_EXPIRES": self.JWT_REFRESH_TOKEN_EXPIRES,
            "JWT_ALGORITHM": self.JWT_ALGORITHM,
            "JWT_TOKEN_LOCATION": self.JWT_TOKEN_LOCATION,
            "JWT_HEADER_NAME": self.JWT_HEADER_NAME,
            "JWT_HEADER_TYPE": self.JWT_HEADER_TYPE,
            "RATELIMIT_DEFAULT": self.RATE_LIMIT,
            "RATELIMIT_STORAGE_URI": self.RATE_LIMIT_STORAGE_URL,
            "MAX_CONTENT_LENGTH": self.MAX_CONTENT_LENGTH,
            "UPLOAD_FOLDER": self.UPLOAD_FOLDER,
        }
