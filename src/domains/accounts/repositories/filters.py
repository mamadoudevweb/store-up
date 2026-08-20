"""Filters for accounts domain."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.core.entities.pagination import EntityFilter

@dataclass(kw_only=True)
class AccountFilter(EntityFilter):
    id: UUID | None = None
    search: str | None = None
    status: str | None = None

@dataclass(kw_only=True)
class CredentialFilter(EntityFilter):
    id: UUID | None = None
    account_id: UUID | None = None
    username: str | None = None
    email: str | None = None
    username_or_email: str | None = None

@dataclass(kw_only=True)
class AccountRoleFilter(EntityFilter):
    account_id: UUID | None = None
    role_id: UUID | None = None
