from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import Select

from src.core.entities.pagination import EntityFilter
from src.domains.sale.repositories.sql.orms import SaleModel, RefundModel


@dataclass(kw_only=True)
class SaleFilters(EntityFilter):
    status: str | None = None
    seller_account_id: uuid.UUID | None = None
    customer_name: str | None = None

    def apply(self, stmt: Select[tuple[Any, ...]]) -> Select[tuple[Any, ...]]:
        """
        Apply the configured filters to a sale query.
        
        Parameters:
        	stmt (Select[tuple[Any, ...]]): The sale query to filter.
        
        Returns:
        	Select[tuple[Any, ...]]: The query with the configured status, seller account, and customer name filters applied.
        """
        if self.status:
            stmt = stmt.where(SaleModel.status == self.status)
        if self.seller_account_id:
            stmt = stmt.where(SaleModel.seller_account_id == self.seller_account_id)
        if self.customer_name:
            stmt = stmt.where(SaleModel.customer_name.ilike(f"%{self.customer_name}%"))
        return stmt


@dataclass(kw_only=True)
class RefundFilters(EntityFilter):
    sale_id: uuid.UUID | None = None
    status: str | None = None

    def apply(self, stmt: Select[tuple[Any, ...]]) -> Select[tuple[Any, ...]]:
        """
        Apply the configured sale and status filters to a refund query.
        
        Parameters:
        	stmt (Select[tuple[Any, ...]]): The refund query to filter.
        
        Returns:
        	Select[tuple[Any, ...]]: The query with the configured filters applied.
        """
        if self.sale_id:
            stmt = stmt.where(RefundModel.sale_id == self.sale_id)
        if self.status:
            stmt = stmt.where(RefundModel.status == self.status)
        return stmt
