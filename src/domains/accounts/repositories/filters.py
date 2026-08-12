"""Filters for accounts domain."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.domains.shared.filters import BaseFilter


@dataclass
class AccountFilter(BaseFilter):
    id: UUID | None = None
    search: str | None = None
    status: str | None = None


@dataclass
class CredentialFilter(BaseFilter):
    id: UUID | None = None
    account_id: UUID | None = None
    username: str | None = None
    email: str | None = None
    username_or_email: str | None = None


@dataclass
class AccountRoleFilter(BaseFilter):
    account_id: UUID | None = None
    role_id: UUID | None = None
