"""SQL Product repository."""
from __future__ import annotations

from typing import Any

from sqlalchemy import exists as sql_exists, select

from src.core.repositories.sql.base_sql_repository import BaseSqlRepository
from src.domains.catalog.entities import Product
from src.domains.catalog.repositories.filters import ProductFilter
from src.domains.catalog.repositories.sql.orms import ProductModel
from src.domains.catalog.repositories.utils import ProductMapper


class SqlProductRepository(BaseSqlRepository[Product, ProductFilter]):
    model = ProductModel
    mapper = ProductMapper()
    filter_cls = ProductFilter

    def _apply_filter(self, query: Any, entity_filter: ProductFilter) -> Any:
        q = query
        if entity_filter.id:
            q = q.where(ProductModel.id == entity_filter.id)
        if entity_filter.sku:
            q = q.where(ProductModel.sku == entity_filter.sku)
        if entity_filter.name:
            q = q.where(ProductModel.name.ilike(f"%{entity_filter.name}%"))
        if entity_filter.category_id:
            q = q.where(ProductModel.category_id == entity_filter.category_id)
        if entity_filter.brand_id:
            q = q.where(ProductModel.brand_id == entity_filter.brand_id)
        if entity_filter.is_active is not None:
            q = q.where(ProductModel.is_active == entity_filter.is_active)
        if entity_filter.sort_by:
            col = getattr(ProductModel, entity_filter.sort_by, None)
            if col is not None:
                q = q.order_by(col.desc() if entity_filter.sort_desc else col.asc())
        return q

    def exists(self, **kwargs: Any) -> bool:
        entity_filter = kwargs.pop("entity_filter", None)
        if entity_filter is None:
            entity_filter = ProductFilter(**kwargs)
        sub = select(ProductModel)
        sub = self._apply_filter(sub, entity_filter)
        stmt = select(sql_exists(sub.subquery()))
        return self._session.scalar(stmt) or False
