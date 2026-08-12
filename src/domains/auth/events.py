"""Auth domain events."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.domains.shared.events import Event


@dataclass
class UserLoggedIn(Event):
    account_id: UUID
    username: str
    ip_address: str | None = None


@dataclass
class UserLoggedOut(Event):
    jti: str
