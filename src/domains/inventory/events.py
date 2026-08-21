"""Events for the Inventory domain."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.core.entities.events import DomainEvent


@dataclass(frozen=True)
class StockAdjusted(DomainEvent):
    """Emitted when stock is physically added or removed (quantity_on_hand changes)."""
    product_id: uuid.UUID
    quantity_change: int
    new_quantity_on_hand: int


@dataclass(frozen=True)
class StockReserved(DomainEvent):
    """Emitted when stock is reserved for an order."""
    product_id: uuid.UUID
    quantity: int
    reference_id: str | None


@dataclass(frozen=True)
class StockReleased(DomainEvent):
    """Emitted when reserved stock is released back (e.g. order cancelled)."""
    product_id: uuid.UUID
    quantity: int
    reference_id: str | None


@dataclass(frozen=True)
class StockShipped(DomainEvent):
    """Emitted when reserved stock is shipped."""
    product_id: uuid.UUID
    quantity: int
    reference_id: str | None


@dataclass(frozen=True)
class LowStockAlert(DomainEvent):
    """Emitted when the available quantity drops below the threshold."""
    product_id: uuid.UUID
    available_quantity: int
    threshold: int


@dataclass(frozen=True)
class OutOfStock(DomainEvent):
    """Emitted when the available quantity reaches zero."""
    product_id: uuid.UUID
