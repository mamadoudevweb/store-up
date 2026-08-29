"""Events for the Stock domain."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.core.entities.events import DomainEvent
from src.domains.stock.entities.enums import ReferenceType


@dataclass(frozen=True)
class StockItemCreated(DomainEvent):
    """Emitted when a new stock item is created."""
    stock_item_id: uuid.UUID
    variant_id: uuid.UUID


@dataclass(frozen=True)
class StockAdjusted(DomainEvent):
    """Emitted when stock is physically added or removed (quantity_on_hand changes)."""
    stock_item_id: uuid.UUID
    variant_id: uuid.UUID
    quantity_change: int
    new_quantity_on_hand: int


@dataclass(frozen=True)
class StockReserved(DomainEvent):
    """Emitted when stock is reserved for an order."""
    stock_item_id: uuid.UUID
    variant_id: uuid.UUID
    quantity: int
    reference_type: ReferenceType
    reference_id: str | None


@dataclass(frozen=True)
class StockReservationFailed(DomainEvent):
    """Emitted when stock reservation fails (e.g. insufficient quantity)."""
    variant_id: uuid.UUID
    quantity: int
    reference_type: ReferenceType
    reference_id: str | None
    reason: str


@dataclass(frozen=True)
class StockReleased(DomainEvent):
    """Emitted when reserved stock is released back (e.g. order cancelled)."""
    stock_item_id: uuid.UUID
    variant_id: uuid.UUID
    quantity: int
    reference_type: ReferenceType
    reference_id: str | None


@dataclass(frozen=True)
class StockShipped(DomainEvent):
    """Emitted when reserved stock is shipped."""
    stock_item_id: uuid.UUID
    variant_id: uuid.UUID
    quantity: int
    reference_type: ReferenceType
    reference_id: str | None


@dataclass(frozen=True)
class LowStockAlert(DomainEvent):
    """Emitted when the available quantity drops below the threshold."""
    stock_item_id: uuid.UUID
    variant_id: uuid.UUID
    available_quantity: int
    threshold: int


@dataclass(frozen=True)
class OutOfStock(DomainEvent):
    """Emitted when the available quantity reaches zero."""
    stock_item_id: uuid.UUID
    variant_id: uuid.UUID
