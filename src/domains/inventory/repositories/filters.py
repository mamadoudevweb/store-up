"""Filters for the Inventory domain."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.core.entities.pagination import EntityFilter


@dataclass(kw_only=True)
class InventoryItemFilter(EntityFilter):
    id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None


@dataclass(kw_only=True)
class StockMovementFilter(EntityFilter):
    id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    reason: str | None = None
    reference_id: str | None = None
