"""Base repository contract."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from .pagination import Paginated

E = TypeVar("E")
F = TypeVar("F")


class BaseRepository(ABC, Generic[E, F]):
    """Generic repository contract for all entities."""

    @abstractmethod
    def add(self, entity: E) -> E:
        """Add a new entity."""
        ...

    @abstractmethod
    def get(self, filters: F) -> E | None:
        """Get a single entity matching the filters."""
        ...

    @abstractmethod
    def exists(self, filters: F) -> bool:
        """Check if any entity matching the filters exists."""
        ...

    @abstractmethod
    def list(self, filters: F) -> Paginated[E]:
        """List entities matching the given filters."""
        ...

    @abstractmethod
    def _apply_filter(self, query: object, filters: F) -> object:
        """Apply filters to the underlying query."""
        ...

    @abstractmethod
    def update(self, entity: E) -> E:
        """Update an existing entity."""
        ...

    @abstractmethod
    def delete(self, entity: E) -> None:
        """Delete an entity."""
        ...
