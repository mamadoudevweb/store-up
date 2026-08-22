"""In-memory token denylist — for development and testing only."""
from __future__ import annotations

from datetime import datetime, timezone

from src.domains.auth.repositories.base_denylist import DenylistRepository


class MemoryDenylistRepository(DenylistRepository):
    """Non-persistent, process-local denylist. Not suitable for multi-process production."""

    def __init__(self) -> None:
        self._store: dict[str, int] = {}  # jti -> unix expiry timestamp

    def add(self, jti: str, exp: datetime | int) -> None:
        if isinstance(exp, datetime):
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            exp = int(exp.timestamp())
        self._store[jti] = exp

    def is_revoked(self, jti: str) -> bool:
        if jti not in self._store:
            return False
        # Prune if already expired (token would be rejected by JWT middleware anyway)
        if self._store[jti] < int(datetime.now(timezone.utc).timestamp()):
            del self._store[jti]
            return False
        return True
