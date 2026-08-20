from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")

@dataclass(kw_only=True)
class Pagination(Generic[T]):
    items: list[T]
    page: int
    limit: int
    total: int

    @property
    def total_pages(self) -> int:
        return max(1, -(-self.total // self.limit))

@dataclass(kw_only=True)
class EntityFilter:
    page: int = 1
    limit: int = 20
    sort_by: str | None = None
    sort_desc: bool = False
