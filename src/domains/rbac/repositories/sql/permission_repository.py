"""SQL implementation of Permission repository."""
from __future__ import annotations
from typing import Any

from sqlalchemy import select

from src.core.repositories.sql.base_sql_repository import BaseSqlRepository
from src.domains.rbac.entities import Permission
from src.domains.rbac.repositories.filters import PermissionFilter
from src.domains.rbac.repositories.sql.orms import PermissionModel, RolePermissionModel
from src.domains.rbac.repositories.utils import PermissionMapper

class SqlPermissionRepository(BaseSqlRepository[Permission, PermissionFilter]):
    model = PermissionModel
    mapper = PermissionMapper()
    filter_cls = PermissionFilter

    def _apply_filter(self, query: Any, entity_filter: PermissionFilter) -> Any:
        q = query
        if entity_filter.id:
            q = q.where(PermissionModel.id == entity_filter.id)
        if entity_filter.resource:
            q = q.where(PermissionModel.resource == entity_filter.resource)
        if entity_filter.action:
            q = q.where(PermissionModel.action == entity_filter.action)
        if entity_filter.role_id:
            q = q.join(RolePermissionModel, RolePermissionModel.permission_id == PermissionModel.id)\
                 .where(RolePermissionModel.role_id == entity_filter.role_id)
        return q
