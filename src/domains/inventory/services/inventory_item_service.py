"""Inventory Item service."""
from __future__ import annotations

import uuid

from src.core.entities.pagination import Pagination
from src.core.repositories.base_repository import EntityId
from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.result import ServiceResult
from src.domains.inventory.entities import InventoryItem, StockMovement
from src.domains.inventory.exceptions import (
    InsufficientReservedStockError,
    InsufficientStockError,
    InventoryItemNotFound,
)
from src.domains.inventory.repositories.filters import InventoryItemFilter


class InventoryItemService(BaseService):
    def get_inventory_item(self, actor: SupportsPermissionCheck, criteria: EntityId | InventoryItemFilter) -> ServiceResult[InventoryItem]:
        self._authorize(actor, "inventory", "inventory_item", "read")
        with self._uow_factory() as uow:
            item = uow.inventory_items.get(criteria)
        if item is None:
            raise InventoryItemNotFound(criteria=criteria)
        return ServiceResult(data=item)

    def list_inventory_items(self, actor: SupportsPermissionCheck, filter_: InventoryItemFilter) -> ServiceResult[Pagination[InventoryItem]]:
        self._authorize(actor, "inventory", "inventory_item", "read")
        with self._uow_factory() as uow:
            page = uow.inventory_items.list(filter_)
        return ServiceResult(data=page)

    def set_low_stock_threshold(self, actor: SupportsPermissionCheck, product_id: uuid.UUID, threshold: int) -> ServiceResult[InventoryItem]:
        self._authorize(actor, "inventory", "inventory_item", "update")
        with self._uow_factory() as uow:
            item = uow.inventory_items.get(InventoryItemFilter(product_id=product_id))
            if not item:
                raise InventoryItemNotFound(product_id=product_id)
            
            item.low_stock_threshold = threshold
            item = uow.inventory_items.update(item)
            uow.track(item)
        return ServiceResult(data=item)

    def adjust_stock(
        self,
        actor: SupportsPermissionCheck,
        product_id: uuid.UUID,
        quantity_change: int,
        reason: str,
        reference_id: str | None = None,
    ) -> ServiceResult[InventoryItem]:
        self._authorize(actor, "inventory", "inventory_item", "update")
        with self._uow_factory() as uow:
            item = uow.inventory_items.get(InventoryItemFilter(product_id=product_id))
            if not item:
                raise InventoryItemNotFound(product_id=product_id)
                
            if quantity_change < 0 and item.quantity_on_hand + quantity_change < item.quantity_reserved:
                raise InsufficientStockError(
                    f"Cannot reduce stock by {abs(quantity_change)}. Currently on hand: {item.quantity_on_hand}, reserved: {item.quantity_reserved}"
                )

            item.adjust_stock(quantity_change)
            item = uow.inventory_items.update(item)
            uow.track(item)
            
            # Record movement
            movement = StockMovement.create(
                product_id=product_id,
                quantity_change=quantity_change,
                reason=reason,
                reference_id=reference_id,
            )
            uow.stock_movements.add(movement)
            
        return ServiceResult(data=item)

    def reserve_stock(
        self, actor: SupportsPermissionCheck, product_id: uuid.UUID, quantity: int, reference_id: str | None = None
    ) -> ServiceResult[InventoryItem]:
        self._authorize(actor, "inventory", "inventory_item", "update")
        with self._uow_factory() as uow:
            item = uow.inventory_items.get(InventoryItemFilter(product_id=product_id))
            if not item:
                raise InventoryItemNotFound(product_id=product_id)

            try:
                item.reserve_stock(quantity, reference_id)
            except ValueError as e:
                raise InsufficientStockError(str(e))

            item = uow.inventory_items.update(item)
            uow.track(item)
        return ServiceResult(data=item)

    def release_stock(
        self, actor: SupportsPermissionCheck, product_id: uuid.UUID, quantity: int, reference_id: str | None = None
    ) -> ServiceResult[InventoryItem]:
        self._authorize(actor, "inventory", "inventory_item", "update")
        with self._uow_factory() as uow:
            item = uow.inventory_items.get(InventoryItemFilter(product_id=product_id))
            if not item:
                raise InventoryItemNotFound(product_id=product_id)

            try:
                item.release_stock(quantity, reference_id)
            except ValueError as e:
                raise InsufficientReservedStockError(str(e))

            item = uow.inventory_items.update(item)
            uow.track(item)
        return ServiceResult(data=item)

    def ship_stock(
        self, actor: SupportsPermissionCheck, product_id: uuid.UUID, quantity: int, reference_id: str | None = None
    ) -> ServiceResult[InventoryItem]:
        self._authorize(actor, "inventory", "inventory_item", "update")
        with self._uow_factory() as uow:
            item = uow.inventory_items.get(InventoryItemFilter(product_id=product_id))
            if not item:
                raise InventoryItemNotFound(product_id=product_id)

            try:
                item.ship_stock(quantity, reference_id)
            except ValueError as e:
                raise InsufficientReservedStockError(str(e))

            item = uow.inventory_items.update(item)
            uow.track(item)
            
            # Record negative physical movement
            movement = StockMovement.create(
                product_id=product_id,
                quantity_change=-quantity,
                reason="ORDER_SHIPPED",
                reference_id=reference_id,
            )
            uow.stock_movements.add(movement)
            
        return ServiceResult(data=item)
