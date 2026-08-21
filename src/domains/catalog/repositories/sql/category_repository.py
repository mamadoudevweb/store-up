"""SQL Category repository."""
from __future__ import annotations

from typing import Any

from sqlalchemy import exists as sql_exists, select

from src.core.repositories.sql.base_sql_repository import BaseSqlRepository
from src.domains.catalog.entities import Category
from src.domains.catalog.repositories.filters import CategoryFilter
from src.domains.catalog.repositories.sql.orms import CategoryModel
from src.domains.catalog.repositories.utils import CategoryMapper


class SqlCategoryRepository(BaseSqlRepository[Category, CategoryFilter]):
    model = CategoryModel
    mapper = CategoryMapper()
    filter_cls = CategoryFilter

    def _apply_filter(self, query: Any, entity_filter: CategoryFilter) -> Any:
        q = query
        if entity_filter.id:
            q = q.where(CategoryModel.id == entity_filter.id)
        if entity_filter.name:
            q = q.where(CategoryModel.name.ilike(f"%{entity_filter.name}%"))
        if entity_filter.parent_id:
            q = q.where(CategoryModel.parent_id == entity_filter.parent_id)
        return q

    def exists(self, entity_filter: CategoryFilter) -> bool:
        sub = select(CategoryModel)
        sub = self._apply_filter(sub, entity_filter)
        stmt = select(sql_exists(sub.subquery()))
        return self._session.scalar(stmt) or False
