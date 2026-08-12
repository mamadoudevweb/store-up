"""Pagination value objects."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class PaginationMeta:
    page: int
    limit: int
    total: int

    @property
    def total_pages(self) -> int:
        if self.limit == 0:
            return 0
        return (self.total + self.limit - 1) // self.limit

    def to_dict(self) -> dict[str, int]:
        return {
            "page": self.page,
            "limit": self.limit,
            "total": self.total,
            "total_pages": self.total_pages,
        }


@dataclass(frozen=True)
class Paginated(Generic[T]):
    """Wrapper returned by all repository .list() calls."""

    items: list[T]
    meta: PaginationMeta

    @classmethod
    def empty(cls, page: int = 1, limit: int = 20) -> "Paginated[T]":
        return cls(items=[], meta=PaginationMeta(page=page, limit=limit, total=0))
