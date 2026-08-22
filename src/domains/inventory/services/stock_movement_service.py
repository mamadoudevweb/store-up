"""Stock Movement service."""
from __future__ import annotations

import uuid

from src.core.entities.pagination import Pagination
from src.core.repositories.base_repository import EntityId
from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.result import ServiceResult
from src.domains.inventory.entities import StockMovement
from src.domains.inventory.exceptions import StockMovementNotFound
from src.domains.inventory.repositories.filters import StockMovementFilter


class StockMovementService(BaseService):
    def get_movement(self, actor: SupportsPermissionCheck, criteria: EntityId | StockMovementFilter) -> ServiceResult[StockMovement]:
        self._authorize(actor, "inventory", "stock_movement", "read")
        with self._uow_factory() as uow:
            movement = uow.stock_movements.get(criteria)
        if movement is None:
            raise StockMovementNotFound(criteria=criteria)
        return ServiceResult(data=movement)

    def list_movements(self, actor: SupportsPermissionCheck, filter_: StockMovementFilter) -> ServiceResult[Pagination[StockMovement]]:
        self._authorize(actor, "inventory", "stock_movement", "read")
        with self._uow_factory() as uow:
            page = uow.stock_movements.list(filter_)
        return ServiceResult(data=page)
