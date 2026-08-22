"""Inventory domain service facade."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.domains.inventory.services.inventory_item_service import InventoryItemService
    from src.domains.inventory.services.stock_movement_service import StockMovementService

class InventoryDomainService:
    """Aggregates inventory entity services."""
    if TYPE_CHECKING:
        item: InventoryItemService
        movement: StockMovementService

    def __init__(self, **entity_services: Any) -> None:
        self.__dict__.update(entity_services)
