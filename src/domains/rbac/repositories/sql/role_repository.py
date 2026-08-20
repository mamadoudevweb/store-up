"""SQL implementation of Role repository."""
from __future__ import annotations
from typing import Any

from sqlalchemy import select

from src.core.repositories.sql.base_sql_repository import BaseSqlRepository
from src.domains.rbac.entities import Role
from src.domains.rbac.repositories.filters import RoleFilter
from src.domains.rbac.repositories.sql.orms import RoleModel
from src.domains.rbac.repositories.utils import RoleMapper

class SqlRoleRepository(BaseSqlRepository[Role, RoleFilter]):
    model = RoleModel
    mapper = RoleMapper()
    filter_cls = RoleFilter

    def _apply_filter(self, query: Any, entity_filter: RoleFilter) -> Any:
        q = query
        if entity_filter.id:
            q = q.where(RoleModel.id == entity_filter.id)
        if entity_filter.name:
            q = q.where(RoleModel.name == entity_filter.name)
        return q
