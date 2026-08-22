"""InventoryItem entity."""
from __future__ import annotations
from uuid import UUID

import uuid
from dataclasses import dataclass

from src.core.entities.base_entity import BaseEntity
from src.domains.inventory.events import LowStockAlert, OutOfStock, StockAdjusted, StockReserved, StockReleased, StockShipped


@dataclass(kw_only=True)
class InventoryItem(BaseEntity[UUID]):
    id: uuid.UUID
    product_id: uuid.UUID
    quantity_on_hand: int = 0
    quantity_reserved: int = 0
    low_stock_threshold: int = 0

    @property
    def available_quantity(self) -> int:
        return self.quantity_on_hand - self.quantity_reserved

    @classmethod
    def create(cls, product_id: uuid.UUID, low_stock_threshold: int = 0) -> InventoryItem:
        return cls(
            id=uuid.uuid4(),
            product_id=product_id,
            quantity_on_hand=0,
            quantity_reserved=0,
            low_stock_threshold=low_stock_threshold,
        )

    def _check_thresholds(self) -> None:
        if self.available_quantity == 0:
            self.register_event(OutOfStock(product_id=self.product_id))
        elif self.available_quantity <= self.low_stock_threshold:
            self.register_event(
                LowStockAlert(
                    product_id=self.product_id,
                    available_quantity=self.available_quantity,
                    threshold=self.low_stock_threshold,
                )
            )

    def adjust_stock(self, quantity_change: int) -> None:
        """Physical addition or removal of stock."""
        self.quantity_on_hand += quantity_change
        self.register_event(
            StockAdjusted(
                product_id=self.product_id,
                quantity_change=quantity_change,
                new_quantity_on_hand=self.quantity_on_hand,
            )
        )
        self._check_thresholds()

    def reserve_stock(self, quantity: int, reference_id: str | None = None) -> None:
        """Reserves stock for an order without removing it physically yet."""
        if quantity > self.available_quantity:
            raise ValueError(f"Cannot reserve {quantity}, only {self.available_quantity} available.")
        self.quantity_reserved += quantity
        self.register_event(
            StockReserved(product_id=self.product_id, quantity=quantity, reference_id=reference_id)
        )
        self._check_thresholds()

    def release_stock(self, quantity: int, reference_id: str | None = None) -> None:
        """Releases reserved stock back to available."""
        if quantity > self.quantity_reserved:
            raise ValueError(f"Cannot release {quantity}, only {self.quantity_reserved} reserved.")
        self.quantity_reserved -= quantity
        self.register_event(
            StockReleased(product_id=self.product_id, quantity=quantity, reference_id=reference_id)
        )
        # Note: Releasing stock increases available quantity, so we don't trigger LowStockAlert here.

    def ship_stock(self, quantity: int, reference_id: str | None = None) -> None:
        """Ships reserved stock, physically removing it."""
        if quantity > self.quantity_reserved:
            raise ValueError(f"Cannot ship {quantity}, only {self.quantity_reserved} reserved.")
        if quantity > self.quantity_on_hand:
             raise ValueError(f"Cannot ship {quantity}, only {self.quantity_on_hand} on hand.")
             
        self.quantity_reserved -= quantity
        self.quantity_on_hand -= quantity
        self.register_event(
            StockShipped(product_id=self.product_id, quantity=quantity, reference_id=reference_id)
        )
        self._check_thresholds()
