"""SQL Attribute and AttributeValue repositories."""
from __future__ import annotations

from typing import Any

from src.core.repositories.sql.base_sql_repository import BaseSqlRepository
from src.domains.catalog.entities import Attribute, AttributeValue
from src.domains.catalog.repositories.filters import AttributeFilter, AttributeValueFilter
from src.domains.catalog.repositories.sql.orms import AttributeModel, AttributeValueModel
from src.domains.catalog.repositories.utils import AttributeMapper, AttributeValueMapper


class SqlAttributeRepository(BaseSqlRepository[Attribute, AttributeFilter]):
    model = AttributeModel
    mapper = AttributeMapper()
    filter_cls = AttributeFilter

    def _apply_filter(self, query: Any, entity_filter: AttributeFilter) -> Any:
        q = query
        if entity_filter.id:
            q = q.where(AttributeModel.id == entity_filter.id)
        if entity_filter.name:
            q = q.where(AttributeModel.name.ilike(f"%{entity_filter.name}%"))
        return q


class SqlAttributeValueRepository(BaseSqlRepository[AttributeValue, AttributeValueFilter]):
    model = AttributeValueModel
    mapper = AttributeValueMapper()
    filter_cls = AttributeValueFilter

    def _apply_filter(self, query: Any, entity_filter: AttributeValueFilter) -> Any:
        q = query
        if entity_filter.id:
            q = q.where(AttributeValueModel.id == entity_filter.id)
        if entity_filter.attribute_id:
            q = q.where(AttributeValueModel.attribute_id == entity_filter.attribute_id)
        return q
