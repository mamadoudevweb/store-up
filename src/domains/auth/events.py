"""Auth domain events."""
from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from src.core.entities.events import DomainEvent


@dataclass(kw_only=True)
class UserLoggedIn(DomainEvent):
    account_id: UUID
    username: str
    ip_address: str | None = None


@dataclass(kw_only=True)
class UserLoggedOut(DomainEvent):
    jti: str
