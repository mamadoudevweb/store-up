"""SQL ProductVariant repository."""
from __future__ import annotations

from typing import Any

from src.core.repositories.sql.base_sql_repository import BaseSqlRepository
from src.domains.catalog.entities import ProductVariant
from src.domains.catalog.repositories.filters import ProductVariantFilter
from src.domains.catalog.repositories.sql.orms import ProductVariantModel
from src.domains.catalog.repositories.utils import ProductVariantMapper


class SqlProductVariantRepository(BaseSqlRepository[ProductVariant, ProductVariantFilter]):
    model = ProductVariantModel
    mapper = ProductVariantMapper()
    filter_cls = ProductVariantFilter

    def _apply_filter(self, query: Any, entity_filter: ProductVariantFilter) -> Any:
        q = query
        if entity_filter.id:
            q = q.where(ProductVariantModel.id == entity_filter.id)
        if entity_filter.product_id:
            q = q.where(ProductVariantModel.product_id == entity_filter.product_id)
        if entity_filter.sku:
            q = q.where(ProductVariantModel.sku == entity_filter.sku)
        if entity_filter.status:
            q = q.where(ProductVariantModel.status == entity_filter.status)
        if entity_filter.sort_by:
            col = getattr(ProductVariantModel, entity_filter.sort_by, None)
            if col is not None:
                q = q.order_by(col.desc() if entity_filter.sort_desc else col.asc())
        return q
