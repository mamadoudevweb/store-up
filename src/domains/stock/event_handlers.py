"""Stock event handlers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.events.dispatcher import EventDispatcher
from src.domains.catalog.events import VariantCreated
from src.domains.stock.entities.stock_item import StockItem

if TYPE_CHECKING:
    from src.app.domain_service import DomainService


def register(dispatcher: EventDispatcher, domain_service: DomainService) -> None:
    def on_variant_created(event: VariantCreated) -> None:
        """Automatically create a 0-stock item when a new variant is created."""
        # Note: The context manager commits on successful exit
        with domain_service.stock.item._uow_factory() as uow:
            item = StockItem.create(variant_id=event.variant_id, low_stock_threshold=0)
            uow.stock_items.add(item)
            uow.track(item)

    dispatcher.subscribe(VariantCreated, on_variant_created)
