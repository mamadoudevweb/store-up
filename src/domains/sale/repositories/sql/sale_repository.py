import uuid
from typing import Any

from sqlalchemy import Select
from sqlalchemy.orm import joinedload

from src.core.repositories.sql.base_sql_repository import BaseSqlRepository
from src.domains.sale.entities.sale import Sale
from src.domains.sale.repositories.sql.orms import SaleModel
from src.domains.sale.repositories.filters import SaleFilters
from src.domains.sale.repositories.utils import SaleMapper


class SqlSaleRepository(BaseSqlRepository[Sale, SaleFilters]):
    model = SaleModel

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.mapper = SaleMapper()
        self.filter_cls = SaleFilters

    def _apply_filter(self, query: Select[Any], entity_filter: SaleFilters) -> Select[Any]:
        """Apply sale-specific filters to a query.
        
        Parameters:
        	query (Select[Any]): The query to filter.
        	entity_filter (SaleFilters): The filters to apply.
        
        Returns:
        	Select[Any]: The filtered query.
        """
        return entity_filter.apply(query)

    def _apply_default_load_options(self, stmt: Select[tuple[Any, ...]]) -> Select[tuple[Any, ...]]:
        """
        Configure the query to eagerly load sale lines.
        
        Parameters:
        	stmt (Select[tuple[Any, ...]]): The query to configure.
        
        Returns:
        	Select[tuple[Any, ...]]: The query with sale lines configured for eager loading.
        """
        return stmt.options(joinedload(SaleModel.lines))

    def _get_entity_id(self, entity: Sale) -> uuid.UUID:
        """Return the UUID identifier of a sale entity.
        
        Parameters:
        	entity (Sale): The sale entity whose identifier is retrieved.
        
        Returns:
        	uuid.UUID: The sale entity's identifier.
        """
        return entity.id
