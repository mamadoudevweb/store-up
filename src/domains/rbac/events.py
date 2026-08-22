"""RBAC domain events."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.core.entities.events import DomainEvent


@dataclass(kw_only=True, frozen=True)
class RoleCreated(DomainEvent):
    role_id: UUID
    name: str


@dataclass(kw_only=True, frozen=True)
class RoleUpdated(DomainEvent):
    role_id: UUID
    description: str


@dataclass(kw_only=True, frozen=True)
class RoleDeleted(DomainEvent):
    role_id: UUID
    name: str


@dataclass(kw_only=True, frozen=True)
class PermissionCreated(DomainEvent):
    permission_id: UUID
    resource: str
    action: str


@dataclass(kw_only=True, frozen=True)
class RolePermissionAssigned(DomainEvent):
    role_id: UUID
    permission_id: UUID


@dataclass(kw_only=True, frozen=True)
class RolePermissionRevoked(DomainEvent):
    role_id: UUID
    permission_id: UUID
