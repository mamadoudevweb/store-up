"""Filters for the Stock domain."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.core.entities.pagination import EntityFilter
from src.domains.stock.entities.enums import StockMovementReason, ReferenceType


@dataclass(kw_only=True)
class StockItemFilter(EntityFilter):
    id: uuid.UUID | None = None
    variant_id: uuid.UUID | None = None


@dataclass(kw_only=True)
class StockMovementFilter(EntityFilter):
    id: uuid.UUID | None = None
    stock_item_id: uuid.UUID | None = None
    reason: StockMovementReason | None = None
    reference_type: ReferenceType | None = None
    reference_id: str | None = None
