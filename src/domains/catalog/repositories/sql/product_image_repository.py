"""SQL ProductImage repository."""
from __future__ import annotations

from typing import Any

from sqlalchemy import exists as sql_exists, select

from src.core.repositories.sql.base_sql_repository import BaseSqlRepository
from src.domains.catalog.entities import ProductImage
from src.domains.catalog.repositories.filters import ProductImageFilter
from src.domains.catalog.repositories.sql.orms import ProductImageModel
from src.domains.catalog.repositories.utils import ProductImageMapper


class SqlProductImageRepository(BaseSqlRepository[ProductImage, ProductImageFilter]):
    model = ProductImageModel
    mapper = ProductImageMapper()
    filter_cls = ProductImageFilter

    def _apply_filter(self, query: Any, entity_filter: ProductImageFilter) -> Any:
        q = query
        if entity_filter.id:
            q = q.where(ProductImageModel.id == entity_filter.id)
        if entity_filter.product_id:
            q = q.where(ProductImageModel.product_id == entity_filter.product_id)
        if entity_filter.is_primary is not None:
            q = q.where(ProductImageModel.is_primary == entity_filter.is_primary)
        # Always order by sort_order for predictable image ordering
        q = q.order_by(ProductImageModel.sort_order)
        return q

    def exists(self, **kwargs: Any) -> bool:
        entity_filter = kwargs.pop("entity_filter", None)
        if entity_filter is None:
            entity_filter = ProductImageFilter(**kwargs)
        sub = select(ProductImageModel)
        sub = self._apply_filter(sub, entity_filter)
        stmt = select(sql_exists(sub.subquery()))
        return self._session.scalar(stmt) or False
