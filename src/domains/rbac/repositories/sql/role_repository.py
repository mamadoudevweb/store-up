"""SQL Role repository."""
from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from src.domains.rbac.entities import Role
from src.domains.rbac.repositories.filters import RoleFilter
from src.domains.rbac.repositories.sql.orms import RoleModel
from src.domains.rbac.repositories.utils import map_role_to_entity, map_role_to_model
from src.domains.shared.pagination import Paginated, PaginationMeta
from src.domains.shared.repositories import BaseRepository


class SqlRoleRepository(BaseRepository[Role, RoleFilter]):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entity: Role) -> Role:
        model = map_role_to_model(entity)
        self._session.add(model)
        self._session.flush()
        return entity

    def get(self, filters: RoleFilter) -> Role | None:
        query = select(RoleModel)
        query = self._apply_filter(query, filters)
        model = self._session.scalar(query.limit(1))
        return map_role_to_entity(model) if model else None

    def exists(self, filters: RoleFilter) -> bool:
        from sqlalchemy import exists as sql_exists
        query = select(RoleModel)
        query = self._apply_filter(query, filters)
        stmt = select(sql_exists(query.subquery()))
        return self._session.scalar(stmt) or False

    def list(self, filters: RoleFilter) -> Paginated[Role]:
        query = select(RoleModel)
        query = self._apply_filter(query, filters)

        count_q = select(func.count()).select_from(RoleModel)
        count_q = self._apply_filter(count_q, filters)
        total = self._session.scalar(count_q) or 0

        query = query.offset(filters.offset).limit(filters.limit)
        models = self._session.scalars(query).all()
        return Paginated(
            items=[map_role_to_entity(m) for m in models],
            meta=PaginationMeta(page=filters.page, limit=filters.limit, total=total),
        )

    def _apply_filter(self, query: object, filters: RoleFilter) -> object:
        from sqlalchemy import Select
        q: Select = query  # type: ignore[assignment]
        if filters.id:
            q = q.where(RoleModel.id == filters.id)
        if filters.name:
            q = q.where(RoleModel.name == filters.name)
        return q

    def update(self, entity: Role) -> Role:
        model = self._session.get(RoleModel, entity.id)
        if model:
            model.name = entity.name
            model.description = entity.description
            model.updated_at = entity.updated_at
            self._session.flush()
        return entity

    def delete(self, entity: Role) -> None:
        model = self._session.get(RoleModel, entity.id)
        if model:
            self._session.delete(model)
            self._session.flush()
