"""InventoryItem repository."""
from __future__ import annotations

from typing import Any

from sqlalchemy.sql import Select

from src.core.repositories.sql.base_sql_repository import BaseSqlRepository
from src.domains.inventory.entities import InventoryItem
from src.domains.inventory.repositories.filters import InventoryItemFilter
from src.domains.inventory.repositories.sql.orms import InventoryItemModel
from src.domains.inventory.repositories.utils import InventoryItemMapper


class SqlInventoryItemRepository(BaseSqlRepository[InventoryItem, InventoryItemFilter]):
    model = InventoryItemModel
    mapper = InventoryItemMapper()
    filter_cls = InventoryItemFilter

    def _apply_filter(self, query: Select[Any], f: InventoryItemFilter) -> Select[Any]:
        if getattr(f, "id", None):
            query = query.where(InventoryItemModel.id == f.id)
        if getattr(f, "product_id", None):
            query = query.where(InventoryItemModel.product_id == f.product_id)
            
        if f.sort_by:
            col = getattr(InventoryItemModel, f.sort_by)
            query = query.order_by(col.desc() if f.sort_desc else col.asc())
        return query
