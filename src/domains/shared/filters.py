"""Base filter for repository list() queries."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BaseFilter:
    """Common pagination params — all domain filters extend this."""

    page: int = 1
    limit: int = 20

    def __post_init__(self) -> None:
        if self.page < 1:
            self.page = 1
        if self.limit < 1 or self.limit > 100:
            self.limit = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit
