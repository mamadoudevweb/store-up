"""Inventory domain service facade."""
from __future__ import annotations

from typing import Any


class InventoryDomainService:
    """Aggregates inventory entity services."""
    def __init__(self, **entity_services: Any) -> None:
        self.__dict__.update(entity_services)
