from typing import Any
from sqlalchemy import select, func
from sqlalchemy.sql import Select
from sqlalchemy.orm import Session
from src.core.repositories.base_repository import BaseRepository, EntityId, E, F
from src.core.repositories.utils import Mapper
from src.core.entities.pagination import Pagination

class BaseSqlRepository(BaseRepository[E, F]):
    model: type[Any]           # ORM model class — set by subclass
    mapper: Mapper[E, Any]      # Mapper instance — set by subclass
    filter_cls: type[F]         # the EntityFilter subclass this repo accepts — set by subclass

    def __init__(self, session: Session) -> None:
        self._session: Session = session   # injected, never owned

    def add(self, entity: E) -> E:
        model = self.mapper.to_model(entity)
        self._session.add(model)
        self._session.flush()
        return self.mapper.to_entity(model)

    def get(self, criteria: EntityId | F) -> E | None:
        if isinstance(criteria, self.filter_cls):
            query = self._apply_filter(select(self.model), criteria)
            model = self._session.scalars(query.limit(1)).first()
        else:
            model = self._session.get(self.model, criteria)   # criteria is an EntityId
        return self.mapper.to_entity(model) if model else None

    def list(self, entity_filter: F) -> Pagination[E]:
        query = self._apply_filter(select(self.model), entity_filter)
        total: int = self._session.scalar(select(func.count()).select_from(query.subquery())) or 0
        query = query.limit(entity_filter.limit).offset((entity_filter.page - 1) * entity_filter.limit)
        models = self._session.scalars(query).all()
        return Pagination(
            items=[self.mapper.to_entity(m) for m in models],
            page=entity_filter.page, limit=entity_filter.limit, total=total,
        )

    def update(self, entity: E) -> E:
        model = self._session.get(self.model, entity.id)
        if not model:
            return entity
        model = self.mapper.to_model(entity, model)
        self._session.flush()
        return self.mapper.to_entity(model)

    def delete(self, entity: E) -> None:
        model = self._session.get(self.model, entity.id)
        if model:
            self._session.delete(model)
            self._session.flush()

    def exists(self, entity_filter: F) -> bool:
        query = self._apply_filter(select(self.model), entity_filter)
        return self._session.scalar(select(query.exists())) or False

    def _apply_filter(self, query: Select[Any], entity_filter: F) -> Select[Any]:
        raise NotImplementedError
