from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar
from src.core.entities.base_entity import Entity
from src.core.entities.pagination import Pagination, EntityFilter

E = TypeVar("E", bound=Entity)
F = TypeVar("F", bound=EntityFilter)
EntityId = int

class BaseRepository(ABC, Generic[E, F]):
    """Repositories never own a session — it's injected by the UoW.
    No business logic here: execute and query only."""

    @abstractmethod
    def add(self, entity: E) -> E: ...

    @abstractmethod
    def get(self, criteria: EntityId | F) -> E | None:
        """Fetch a single entity — either by primary key (EntityId) or by
        an EntityFilter when the lookup is by some other criteria (e.g. a
        unique sku, an email). If a filter matches more than one row, the
        first by the query's natural order is returned; use list() when
        you actually want every match."""
        ...

    @abstractmethod
    def list(self, entity_filter: F) -> Pagination[E]: ...

    @abstractmethod
    def update(self, entity: E) -> E: ...

    @abstractmethod
    def delete(self, entity: E) -> None: ...

    @abstractmethod
    def exists(self, **kwargs: Any) -> bool: ...

    @abstractmethod
    def _apply_filter(self, query: Any, entity_filter: F) -> Any:
        """Translate an EntityFilter into ORM query clauses only."""
        ...
