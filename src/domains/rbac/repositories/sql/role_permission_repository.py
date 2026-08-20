"""SQL implementation of RolePermission repository."""
from __future__ import annotations
from typing import Any

from sqlalchemy import select

from src.core.repositories.sql.base_sql_repository import BaseSqlRepository
from src.domains.rbac.entities import RolePermission
from src.domains.rbac.repositories.filters import RolePermissionFilter
from src.domains.rbac.repositories.sql.orms import RolePermissionModel
from src.domains.rbac.repositories.utils import RolePermissionMapper

class SqlRolePermissionRepository(BaseSqlRepository[RolePermission, RolePermissionFilter]):
    model = RolePermissionModel
    mapper = RolePermissionMapper()
    filter_cls = RolePermissionFilter

    def _apply_filter(self, query: Any, entity_filter: RolePermissionFilter) -> Any:
        q = query
        if entity_filter.role_id:
            q = q.where(RolePermissionModel.role_id == entity_filter.role_id)
        if entity_filter.permission_id:
            q = q.where(RolePermissionModel.permission_id == entity_filter.permission_id)
        return q

    def update(self, entity: RolePermission) -> RolePermission:
        return entity

    def delete(self, entity: RolePermission) -> None:
        model = self._session.get(self.model, (entity.role_id, entity.permission_id))
        if model:
            self._session.delete(model)
            self._session.flush()
