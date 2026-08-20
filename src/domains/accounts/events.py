"""Accounts domain events — emitted by every account/credential operation."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.core.entities.events import DomainEvent

@dataclass(kw_only=True, frozen=True)
class AccountCreated(DomainEvent):
    account_id: UUID

@dataclass(kw_only=True, frozen=True)
class AccountUpdated(DomainEvent):
    account_id: UUID

@dataclass(kw_only=True, frozen=True)
class AccountSuspended(DomainEvent):
    account_id: UUID

@dataclass(kw_only=True, frozen=True)
class CredentialSet(DomainEvent):
    account_id: UUID
    credential_id: UUID

@dataclass(kw_only=True, frozen=True)
class CredentialUpdated(DomainEvent):
    account_id: UUID

@dataclass(kw_only=True, frozen=True)
class RoleAssigned(DomainEvent):
    account_id: UUID
    role_id: UUID
    domain_scope: str | None = None

@dataclass(kw_only=True, frozen=True)
class RoleRevoked(DomainEvent):
    account_id: UUID
    role_id: UUID
