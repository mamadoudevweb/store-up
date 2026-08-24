"""SQL ProductCategory repository."""
from __future__ import annotations

from typing import Any

from src.core.repositories.sql.base_sql_repository import BaseSqlRepository
from src.domains.catalog.entities import ProductCategory
from src.domains.catalog.repositories.filters import ProductCategoryFilter
from src.domains.catalog.repositories.sql.orms import ProductCategoryModel
from src.domains.catalog.repositories.utils import ProductCategoryMapper


class SqlProductCategoryRepository(BaseSqlRepository[ProductCategory, ProductCategoryFilter]):
    model = ProductCategoryModel
    mapper = ProductCategoryMapper()
    filter_cls = ProductCategoryFilter

    def _apply_filter(self, query: Any, entity_filter: ProductCategoryFilter) -> Any:
        q = query
        if entity_filter.product_id:
            q = q.where(ProductCategoryModel.product_id == entity_filter.product_id)
        if entity_filter.category_id:
            q = q.where(ProductCategoryModel.category_id == entity_filter.category_id)
        return q
