"""Configuration package — exposes get_config() factory."""
from __future__ import annotations

from .base import BaseConfig
from .development import DevelopmentConfig
from .production import ProductionConfig
from .testing import TestingConfig

_CONFIG_MAP: dict[str, type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(env: str = "development") -> BaseConfig:
    """Return the config instance for the given environment name."""
    config_cls = _CONFIG_MAP.get(env, DevelopmentConfig)
    return config_cls()  # type: ignore[return-value]
