"""StockItem repository."""
from __future__ import annotations

from typing import Any, cast
from sqlalchemy.engine import CursorResult

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
        """
        Apply the requested stock item filters and ordering to a query.
        
        Parameters:
        	query (Select[Any]): The query to refine.
        	f (StockItemFilter): Filter and sorting criteria.
        
        Returns:
        	Select[Any]: The query with the specified filters and ordering applied.
        """
        if getattr(f, "id", None):
            query = query.where(StockItemModel.id == f.id)
        if getattr(f, "variant_id", None):
            query = query.where(StockItemModel.variant_id == f.variant_id)
            
        if f.sort_by:
            col = getattr(StockItemModel, f.sort_by)
            query = query.order_by(col.desc() if f.sort_desc else col.asc())
        return query

    def atomic_reserve(self, variant_id: Any, qty: int) -> bool:
        """
        Atomically reserve available stock for a variant.
        
        Parameters:
        	variant_id (Any): Identifier of the variant whose stock is reserved.
        	qty (int): Quantity to reserve.
        
        Returns:
        	bool: `true` if stock was reserved, `false` if insufficient stock or no matching variant exists.
        """
        from sqlalchemy import update
        
        stmt = (
            update(StockItemModel)
            .where(StockItemModel.variant_id == variant_id)
            .where((StockItemModel.quantity_on_hand - StockItemModel.quantity_reserved) >= qty)
            .values(quantity_reserved=StockItemModel.quantity_reserved + qty)
        )
        result = cast(CursorResult[Any], self._session.execute(stmt))
        return result.rowcount > 0

    def atomic_release(self, variant_id: Any, qty: int) -> bool:
        """
        Release reserved stock for a variant when the reserved quantity is sufficient.
        
        Parameters:
        	variant_id (Any): Identifier of the variant whose reserved stock is reduced.
        	qty (int): Quantity to release.
        
        Returns:
        	bool: `true` if reserved stock was released, `false` otherwise.
        """
        from sqlalchemy import update
        
        stmt = (
            update(StockItemModel)
            .where(StockItemModel.variant_id == variant_id)
            .where(StockItemModel.quantity_reserved >= qty)
            .values(quantity_reserved=StockItemModel.quantity_reserved - qty)
        )
        result = cast(CursorResult[Any], self._session.execute(stmt))
        return result.rowcount > 0
