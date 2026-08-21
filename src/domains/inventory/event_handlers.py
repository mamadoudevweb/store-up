"""Inventory event handlers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.events.dispatcher import EventDispatcher
from src.domains.catalog.events import ProductCreated
from src.domains.inventory.entities import InventoryItem

if TYPE_CHECKING:
    from src.app.domain_service import DomainService


def register(dispatcher: EventDispatcher, domain_service: DomainService) -> None:
    def on_product_created(event: ProductCreated) -> None:
        """Automatically create a 0-stock inventory item when a new product is created."""
        # Note: Event handlers typically run within a background task or right after commit.
        # However, to be fully safe and self-contained, the handler opens its own UoW via the service factory.
        with domain_service.inventory.item._uow_factory() as uow:
            item = InventoryItem.create(product_id=event.product_id, low_stock_threshold=0)
            uow.inventory_items.add(item)
            uow.commit()

    dispatcher.subscribe(ProductCreated, on_product_created)
