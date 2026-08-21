"""StockMovement repository."""
from __future__ import annotations

from typing import Any

from sqlalchemy.sql import Select

from src.core.repositories.sql.base_sql_repository import BaseSqlRepository
from src.domains.inventory.entities import StockMovement
from src.domains.inventory.repositories.filters import StockMovementFilter
from src.domains.inventory.repositories.sql.orms import StockMovementModel
from src.domains.inventory.repositories.utils import StockMovementMapper


class SqlStockMovementRepository(BaseSqlRepository[StockMovement, StockMovementFilter]):
    model = StockMovementModel
    mapper = StockMovementMapper()
    filter_cls = StockMovementFilter

    def _apply_filter(self, query: Select[Any], f: StockMovementFilter) -> Select[Any]:
        if getattr(f, "id", None):
            query = query.where(StockMovementModel.id == f.id)
        if getattr(f, "product_id", None):
            query = query.where(StockMovementModel.product_id == f.product_id)
        if getattr(f, "reason", None):
            query = query.where(StockMovementModel.reason == f.reason)
        if getattr(f, "reference_id", None):
            query = query.where(StockMovementModel.reference_id == f.reference_id)
            
        if f.sort_by:
            col = getattr(StockMovementModel, f.sort_by)
            query = query.order_by(col.desc() if f.sort_desc else col.asc())
        else:
            # Default order by created_at desc
            query = query.order_by(StockMovementModel.created_at.desc())
            
        return query
