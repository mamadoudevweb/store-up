import uuid
from typing import Any

from sqlalchemy import Select
from sqlalchemy.orm import joinedload

from src.core.repositories.sql.base_sql_repository import BaseSqlRepository
from src.domains.sale.entities.refund import Refund
from src.domains.sale.repositories.sql.orms import RefundModel
from src.domains.sale.repositories.filters import RefundFilters
from src.domains.sale.repositories.utils import RefundMapper


class SqlRefundRepository(BaseSqlRepository[Refund, RefundFilters]):
    model = RefundModel

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.mapper = RefundMapper()
        self.filter_cls = RefundFilters

    def _apply_filter(self, query: Select[Any], entity_filter: RefundFilters) -> Select[Any]:
        """Apply refund-specific filtering to a SQL query.
        
        Parameters:
        	entity_filter (RefundFilters): Filters used to constrain the query.
        
        Returns:
        	Select[Any]: The filtered SQL query.
        """
        return entity_filter.apply(query)

    def _apply_default_load_options(self, stmt: Select[tuple[Any, ...]]) -> Select[tuple[Any, ...]]:
        """
        Configure the query to eagerly load the refund's lines.
        
        Returns:
            Select[tuple[Any, ...]]: The query with refund lines configured for eager loading.
        """
        return stmt.options(joinedload(RefundModel.lines))

    def _get_entity_id(self, entity: Refund) -> uuid.UUID:
        """Return the UUID identifier of a refund entity.
        
        Parameters:
            entity (Refund): The refund whose identifier is retrieved.
        
        Returns:
            uuid.UUID: The refund entity's UUID identifier.
        """
        return entity.id
