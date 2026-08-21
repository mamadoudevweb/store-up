"""Testing configuration."""
from __future__ import annotations

from .base import BaseConfig


class TestingConfig(BaseConfig):
    FLASK_ENV: str = "testing"
    TESTING: bool = True
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///:memory:"
    REDIS_URL: str = "redis://localhost:6379/15"  # isolated DB index
    RATE_LIMIT: str = "99999 per hour"            # effectively disabled
    RATE_LIMIT_STORAGE_URL: str = "memory://"
    JWT_ACCESS_TOKEN_EXPIRES: int = 300
    SUPERUSER_PASSWORD: str = "test-password"
