"""SQL RolePermission repository."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.domains.rbac.entities import RolePermission
from src.domains.rbac.repositories.filters import RolePermissionFilter
from src.domains.rbac.repositories.sql.orms import RolePermissionModel
from src.domains.shared.pagination import Paginated, PaginationMeta
from src.domains.shared.repositories import BaseRepository


from src.domains.rbac.repositories.utils import (
    map_role_permission_to_entity,
    map_role_permission_to_model,
)


class SqlRolePermissionRepository(BaseRepository[RolePermission, RolePermissionFilter]):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entity: RolePermission) -> RolePermission:
        model = map_role_permission_to_model(entity)
        self._session.add(model)
        self._session.flush()
        return entity

    def get(self, filters: RolePermissionFilter) -> RolePermission | None:
        query = select(RolePermissionModel)
        query = self._apply_filter(query, filters)
        model = self._session.scalar(query.limit(1))
        return map_role_permission_to_entity(model) if model else None

    def exists(self, filters: RolePermissionFilter) -> bool:
        from sqlalchemy import exists as sql_exists
        query = select(RolePermissionModel)
        query = self._apply_filter(query, filters)
        stmt = select(sql_exists(query.subquery()))
        return self._session.scalar(stmt) or False

    def list(self, filters: RolePermissionFilter) -> Paginated[RolePermission]:
        query = select(RolePermissionModel)
        query = self._apply_filter(query, filters)

        count_q = select(func.count()).select_from(RolePermissionModel)
        count_q = self._apply_filter(count_q, filters)
        total = self._session.scalar(count_q) or 0

        query = query.offset(filters.offset).limit(filters.limit)
        models = self._session.scalars(query).all()
        return Paginated(
            items=[map_role_permission_to_entity(m) for m in models],
            meta=PaginationMeta(page=filters.page, limit=filters.limit, total=total),
        )

    def _apply_filter(self, query: object, filters: RolePermissionFilter) -> object:
        from sqlalchemy import Select
        q: Select = query  # type: ignore[assignment]
        if filters.role_id:
            q = q.where(RolePermissionModel.role_id == filters.role_id)
        if filters.permission_id:
            q = q.where(RolePermissionModel.permission_id == filters.permission_id)
        return q

    def update(self, entity: RolePermission) -> RolePermission:
        # RolePermission is a pure join table with no mutable fields
        return entity

    def delete(self, entity: RolePermission) -> None:
        model = self._session.get(
            RolePermissionModel, (entity.role_id, entity.permission_id)
        )
        if model:
            self._session.delete(model)
            self._session.flush()
