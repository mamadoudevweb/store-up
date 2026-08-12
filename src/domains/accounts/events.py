"""Accounts domain events — emitted by every account/credential operation."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.domains.shared.events import DomainEvent


@dataclass
class AccountCreated(DomainEvent):
    event_type: str = "accounts.account.created"  # type: ignore[assignment]
    account_id: UUID = None  # type: ignore[assignment]


@dataclass
class AccountUpdated(DomainEvent):
    event_type: str = "accounts.account.updated"  # type: ignore[assignment]
    account_id: UUID = None  # type: ignore[assignment]


@dataclass
class AccountSuspended(DomainEvent):
    event_type: str = "accounts.account.suspended"  # type: ignore[assignment]
    account_id: UUID = None  # type: ignore[assignment]


@dataclass
class CredentialSet(DomainEvent):
    event_type: str = "accounts.credential.set"  # type: ignore[assignment]
    account_id: UUID = None  # type: ignore[assignment]
    credential_id: UUID = None  # type: ignore[assignment]


@dataclass
class CredentialUpdated(DomainEvent):
    event_type: str = "accounts.credential.updated"  # type: ignore[assignment]
    account_id: UUID = None  # type: ignore[assignment]


@dataclass
class RoleAssigned(DomainEvent):
    event_type: str = "accounts.role.assigned"  # type: ignore[assignment]
    account_id: UUID = None  # type: ignore[assignment]
    role_id: UUID = None  # type: ignore[assignment]
    domain_scope: str | None = None


@dataclass
class RoleRevoked(DomainEvent):
    event_type: str = "accounts.role.revoked"  # type: ignore[assignment]
    account_id: UUID = None  # type: ignore[assignment]
    role_id: UUID = None  # type: ignore[assignment]
