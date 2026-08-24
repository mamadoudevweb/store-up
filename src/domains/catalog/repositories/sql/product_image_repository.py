"""SQL ProductImage repository."""
from __future__ import annotations

from typing import Any

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
        if entity_filter.variant_id:
            q = q.where(ProductImageModel.variant_id == entity_filter.variant_id)
        # Always order by `order` so lowest = primary/cover image
        q = q.order_by(ProductImageModel.order)
        return q
