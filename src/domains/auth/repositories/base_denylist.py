"""Abstract base contract for the token denylist repository."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime


class DenylistRepository(ABC):
    """Contract for token revocation storage."""

    @abstractmethod
    def add(self, jti: str, exp: datetime | int) -> None:
        """Add a revoked token JTI with its expiry."""
        ...

    @abstractmethod
    def is_revoked(self, jti: str) -> bool:
        """Return True if the given JTI has been revoked."""
        ...
