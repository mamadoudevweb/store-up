"""SQL Brand repository."""
from __future__ import annotations

from typing import Any

from sqlalchemy import exists as sql_exists, select

from src.core.repositories.sql.base_sql_repository import BaseSqlRepository
from src.domains.catalog.entities import Brand
from src.domains.catalog.repositories.filters import BrandFilter
from src.domains.catalog.repositories.sql.orms import BrandModel
from src.domains.catalog.repositories.utils import BrandMapper


class SqlBrandRepository(BaseSqlRepository[Brand, BrandFilter]):
    model = BrandModel
    mapper = BrandMapper()
    filter_cls = BrandFilter

    def _apply_filter(self, query: Any, entity_filter: BrandFilter) -> Any:
        q = query
        if entity_filter.id:
            q = q.where(BrandModel.id == entity_filter.id)
        if entity_filter.name:
            q = q.where(BrandModel.name.ilike(f"%{entity_filter.name}%"))
        if entity_filter.is_active is not None:
            q = q.where(BrandModel.is_active == entity_filter.is_active)
        return q

    def exists(self, entity_filter: BrandFilter) -> bool:
        sub = select(BrandModel)
        sub = self._apply_filter(sub, entity_filter)
        stmt = select(sql_exists(sub.subquery()))
        return self._session.scalar(stmt) or False
