"""Development configuration."""
from __future__ import annotations

from .base import BaseConfig


class DevelopmentConfig(BaseConfig):
    FLASK_ENV: str = "development"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./store_up_dev.db"
    RATE_LIMIT: str = "1000 per hour"  # relaxed for dev
    RATE_LIMIT_STORAGE_URL: str = "memory://"
