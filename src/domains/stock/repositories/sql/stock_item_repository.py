"""StockItem repository."""
from __future__ import annotations

from typing import Any

from sqlalchemy.sql import Select

from src.core.repositories.sql.base_sql_repository import BaseSqlRepository
from src.domains.stock.entities import StockItem
from src.domains.stock.repositories.filters import StockItemFilter
from src.domains.stock.repositories.sql.orms import StockItemModel
from src.domains.stock.repositories.utils import StockItemMapper


class SqlStockItemRepository(BaseSqlRepository[StockItem, StockItemFilter]):
    model = StockItemModel
    mapper = StockItemMapper()
    filter_cls = StockItemFilter

    def _apply_filter(self, query: Select[Any], f: StockItemFilter) -> Select[Any]:
        if getattr(f, "id", None):
            query = query.where(StockItemModel.id == f.id)
        if getattr(f, "variant_id", None):
            query = query.where(StockItemModel.variant_id == f.variant_id)
            
        if f.sort_by:
            col = getattr(StockItemModel, f.sort_by)
            query = query.order_by(col.desc() if f.sort_desc else col.asc())
        return query
