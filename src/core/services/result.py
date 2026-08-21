from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")

@dataclass(frozen=True, kw_only=True)
class ServiceResult(Generic[T]):
    data: T
    meta: dict | None = None

    @property
    def success(self) -> bool:
        """Returns True because Services raise AppError on failure."""
        return True
