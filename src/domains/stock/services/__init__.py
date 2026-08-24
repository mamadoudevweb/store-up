"""Stock domain service facade."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.domains.stock.services.stock_item_service import StockItemService
    from src.domains.stock.services.stock_movement_service import StockMovementService

class StockDomainService:
    """Aggregates stock entity services."""
    if TYPE_CHECKING:
        item: StockItemService
        movement: StockMovementService

    def __init__(self, **entity_services: Any) -> None:
        self.__dict__.update(entity_services)
