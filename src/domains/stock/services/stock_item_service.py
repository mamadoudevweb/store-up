"""Stock Item service."""
from __future__ import annotations

import uuid

from src.core.entities.pagination import Pagination
from src.core.repositories.base_repository import EntityId
from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.result import ServiceResult
from src.domains.stock.entities import StockItem, StockMovement
from src.domains.stock.entities.enums import StockMovementReason, ReferenceType
from src.domains.stock.exceptions import (
    InsufficientReservedStockError,
    InsufficientStockError,
    StockItemNotFound,
)
from src.domains.stock.repositories.filters import StockItemFilter


class StockItemService(BaseService):
    def get_stock_item(self, actor: SupportsPermissionCheck, criteria: EntityId | StockItemFilter) -> ServiceResult[StockItem]:
        self._authorize(actor, "stock", "stock_item", "read")
        with self._uow_factory() as uow:
            item = uow.stock_items.get(criteria)
        if item is None:
            raise StockItemNotFound(criteria=criteria)
        return ServiceResult(data=item)

    def list_stock_items(self, actor: SupportsPermissionCheck, filter_: StockItemFilter) -> ServiceResult[Pagination[StockItem]]:
        self._authorize(actor, "stock", "stock_item", "read")
        with self._uow_factory() as uow:
            page = uow.stock_items.list(filter_)
        return ServiceResult(data=page)

    def set_low_stock_threshold(self, actor: SupportsPermissionCheck, variant_id: uuid.UUID, threshold: int) -> ServiceResult[StockItem]:
        self._authorize(actor, "stock", "stock_item", "update")
        with self._uow_factory() as uow:
            item = uow.stock_items.get(StockItemFilter(variant_id=variant_id))
            if not item:
                raise StockItemNotFound(variant_id=variant_id)
            
            item.low_stock_threshold = threshold
            item = uow.stock_items.update(item)
            uow.track(item)
        return ServiceResult(data=item)

    def adjust_stock(
        self,
        actor: SupportsPermissionCheck,
        variant_id: uuid.UUID,
        quantity_change: int,
        reason: StockMovementReason,
        reference_type: ReferenceType,
        reference_id: str | None = None,
    ) -> ServiceResult[StockItem]:
        self._authorize(actor, "stock", "stock_item", "update")
        with self._uow_factory() as uow:
            item = uow.stock_items.get(StockItemFilter(variant_id=variant_id))
            if not item:
                raise StockItemNotFound(variant_id=variant_id)
                
            if quantity_change < 0 and item.quantity_on_hand + quantity_change < item.quantity_reserved:
                raise InsufficientStockError(
                    f"Cannot reduce stock by {abs(quantity_change)}. Currently on hand: {item.quantity_on_hand}, reserved: {item.quantity_reserved}"
                )

            item.adjust_stock(quantity_change)
            item = uow.stock_items.update(item)
            uow.track(item)
            
            # Record movement
            movement = StockMovement.create(
                stock_item_id=item.id,
                quantity_change=quantity_change,
                reason=reason,
                reference_type=reference_type,
                reference_id=reference_id,
            )
            uow.stock_movements.add(movement)
            
        return ServiceResult(data=item)

    def reserve_stock(
        self, actor: SupportsPermissionCheck, variant_id: uuid.UUID, quantity: int, reference_type: ReferenceType, reference_id: str | None = None
    ) -> ServiceResult[StockItem]:
        self._authorize(actor, "stock", "stock_item", "update")
        with self._uow_factory() as uow:
            item = uow.stock_items.get(StockItemFilter(variant_id=variant_id))
            if not item:
                raise StockItemNotFound(variant_id=variant_id)

            try:
                item.reserve_stock(quantity, reference_type, reference_id)
            except ValueError as e:
                raise InsufficientStockError(str(e))

            item = uow.stock_items.update(item)
            uow.track(item)
        return ServiceResult(data=item)

    def release_stock(
        self, actor: SupportsPermissionCheck, variant_id: uuid.UUID, quantity: int, reference_type: ReferenceType, reference_id: str | None = None
    ) -> ServiceResult[StockItem]:
        self._authorize(actor, "stock", "stock_item", "update")
        with self._uow_factory() as uow:
            item = uow.stock_items.get(StockItemFilter(variant_id=variant_id))
            if not item:
                raise StockItemNotFound(variant_id=variant_id)

            try:
                item.release_stock(quantity, reference_type, reference_id)
            except ValueError as e:
                raise InsufficientReservedStockError(str(e))

            item = uow.stock_items.update(item)
            uow.track(item)
        return ServiceResult(data=item)

    def ship_stock(
        self, actor: SupportsPermissionCheck, variant_id: uuid.UUID, quantity: int, reference_type: ReferenceType, reference_id: str | None = None
    ) -> ServiceResult[StockItem]:
        self._authorize(actor, "stock", "stock_item", "update")
        with self._uow_factory() as uow:
            item = uow.stock_items.get(StockItemFilter(variant_id=variant_id))
            if not item:
                raise StockItemNotFound(variant_id=variant_id)

            try:
                item.ship_stock(quantity, reference_type, reference_id)
            except ValueError as e:
                raise InsufficientReservedStockError(str(e))

            item = uow.stock_items.update(item)
            uow.track(item)
            
            # Record negative physical movement
            movement = StockMovement.create(
                stock_item_id=item.id,
                quantity_change=-quantity,
                reason=StockMovementReason.ORDER_SHIPPED,
                reference_type=reference_type,
                reference_id=reference_id,
            )
            uow.stock_movements.add(movement)
            
        return ServiceResult(data=item)
