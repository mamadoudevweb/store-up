"""StockItem entity."""
from __future__ import annotations
from uuid import UUID

import uuid
from dataclasses import dataclass

from src.core.entities.base_entity import BaseEntity
from src.domains.stock.entities.enums import ReferenceType
from src.domains.stock.events import (
    LowStockAlert, 
    OutOfStock, 
    StockAdjusted, 
    StockReserved, 
    StockReleased, 
    StockShipped,
    StockItemCreated
)


@dataclass(kw_only=True)
class StockItem(BaseEntity[UUID]):
    id: uuid.UUID
    variant_id: uuid.UUID
    quantity_on_hand: int = 0
    quantity_reserved: int = 0
    low_stock_threshold: int = 0

    @property
    def available_quantity(self) -> int:
        return self.quantity_on_hand - self.quantity_reserved

    @classmethod
    def create(cls, variant_id: uuid.UUID, low_stock_threshold: int = 0) -> StockItem:
        item = cls(
            id=uuid.uuid4(),
            variant_id=variant_id,
            quantity_on_hand=0,
            quantity_reserved=0,
            low_stock_threshold=low_stock_threshold,
        )
        if item.id is None:
            raise ValueError("item ID cannot be None")
        item.register_event(StockItemCreated(stock_item_id=item.id, variant_id=item.variant_id))
        return item

    def _check_thresholds(self) -> None:
        if self.id is None:
            raise ValueError("self ID cannot be None")
        if self.available_quantity == 0:
            self.register_event(OutOfStock(stock_item_id=self.id, variant_id=self.variant_id))
        elif self.available_quantity <= self.low_stock_threshold:
            self.register_event(
                LowStockAlert(
                    stock_item_id=self.id,
                    variant_id=self.variant_id,
                    available_quantity=self.available_quantity,
                    threshold=self.low_stock_threshold,
                )
            )

    def adjust_stock(self, quantity_change: int) -> None:
        """Physical addition or removal of stock."""
        if self.id is None:
            raise ValueError("self ID cannot be None")
        self.quantity_on_hand += quantity_change
        self.register_event(
            StockAdjusted(
                stock_item_id=self.id,
                variant_id=self.variant_id,
                quantity_change=quantity_change,
                new_quantity_on_hand=self.quantity_on_hand,
            )
        )
        self._check_thresholds()

    def reserve_stock(self, quantity: int, reference_type: ReferenceType, reference_id: str | None = None) -> None:
        """Reserves stock for an order without removing it physically yet."""
        if self.id is None:
            raise ValueError("self ID cannot be None")
        if quantity > self.available_quantity:
            raise ValueError(f"Cannot reserve {quantity}, only {self.available_quantity} available.")
        self.quantity_reserved += quantity
        self.register_event(
            StockReserved(
                stock_item_id=self.id, 
                variant_id=self.variant_id, 
                quantity=quantity, 
                reference_type=reference_type, 
                reference_id=reference_id
            )
        )
        self._check_thresholds()

    def release_stock(self, quantity: int, reference_type: ReferenceType, reference_id: str | None = None) -> None:
        """Releases reserved stock back to available."""
        if self.id is None:
            raise ValueError("self ID cannot be None")
        if quantity > self.quantity_reserved:
            raise ValueError(f"Cannot release {quantity}, only {self.quantity_reserved} reserved.")
        self.quantity_reserved -= quantity
        self.register_event(
            StockReleased(
                stock_item_id=self.id, 
                variant_id=self.variant_id, 
                quantity=quantity, 
                reference_type=reference_type, 
                reference_id=reference_id
            )
        )
        # Note: Releasing stock increases available quantity, so we don't trigger LowStockAlert here.

    def ship_stock(self, quantity: int, reference_type: ReferenceType, reference_id: str | None = None) -> None:
        """Ships reserved stock, physically removing it."""
        if self.id is None:
            raise ValueError("self ID cannot be None")
        if quantity > self.quantity_reserved:
            raise ValueError(f"Cannot ship {quantity}, only {self.quantity_reserved} reserved.")
        if quantity > self.quantity_on_hand:
             raise ValueError(f"Cannot ship {quantity}, only {self.quantity_on_hand} on hand.")
             
        self.quantity_reserved -= quantity
        self.quantity_on_hand -= quantity
        self.register_event(
            StockShipped(
                stock_item_id=self.id, 
                variant_id=self.variant_id, 
                quantity=quantity, 
                reference_type=reference_type, 
                reference_id=reference_id
            )
        )
        self._check_thresholds()
