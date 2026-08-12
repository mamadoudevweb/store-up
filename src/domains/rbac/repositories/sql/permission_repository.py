"""SQL Permission repository."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.domains.rbac.entities import Permission
from src.domains.rbac.repositories.filters import PermissionFilter
from src.domains.rbac.repositories.sql.orms import PermissionModel, RoleModel
from src.domains.rbac.repositories.utils import map_permission_to_entity, map_permission_to_model
from src.domains.shared.pagination import Paginated, PaginationMeta
from src.domains.shared.repositories import BaseRepository


class SqlPermissionRepository(BaseRepository[Permission, PermissionFilter]):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entity: Permission) -> Permission:
        model = map_permission_to_model(entity)
        self._session.add(model)
        self._session.flush()
        return entity

    def get(self, filters: PermissionFilter) -> Permission | None:
        query = select(PermissionModel)
        query = self._apply_filter(query, filters)
        model = self._session.scalar(query.limit(1))
        return map_permission_to_entity(model) if model else None

    def exists(self, filters: PermissionFilter) -> bool:
        from sqlalchemy import exists as sql_exists
        query = select(PermissionModel)
        query = self._apply_filter(query, filters)
        stmt = select(sql_exists(query.subquery()))
        return self._session.scalar(stmt) or False

    def list(self, filters: PermissionFilter) -> Paginated[Permission]:
        query = select(PermissionModel)
        query = self._apply_filter(query, filters)

        count_q = select(func.count()).select_from(PermissionModel)
        count_q = self._apply_filter(count_q, filters)
        total = self._session.scalar(count_q) or 0

        query = query.offset(filters.offset).limit(filters.limit)
        models = self._session.scalars(query).all()
        return Paginated(
            items=[map_permission_to_entity(m) for m in models],
            meta=PaginationMeta(page=filters.page, limit=filters.limit, total=total),
        )

    def _apply_filter(self, query: object, filters: PermissionFilter) -> object:
        from sqlalchemy import Select
        q: Select = query  # type: ignore[assignment]
        if filters.id:
            q = q.where(PermissionModel.id == filters.id)
        if filters.resource:
            q = q.where(PermissionModel.resource == filters.resource)
        if filters.action:
            q = q.where(PermissionModel.action == filters.action)
        if filters.role_id:
            q = q.join(RoleModel, PermissionModel.roles).where(RoleModel.id == filters.role_id)
        return q

    def update(self, entity: Permission) -> Permission:
        model = self._session.get(PermissionModel, entity.id)
        if model:
            model.resource = entity.resource
            model.action = entity.action
            model.description = entity.description
            self._session.flush()
        return entity

    def delete(self, entity: Permission) -> None:
        model = self._session.get(PermissionModel, entity.id)
        if model:
            self._session.delete(model)
            self._session.flush()
