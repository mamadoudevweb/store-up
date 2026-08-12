"""RBAC domain events."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.domains.shared.events import DomainEvent


@dataclass
class RoleCreated(DomainEvent):
    role_id: UUID
    name: str


@dataclass
class PermissionCreated(DomainEvent):
    permission_id: UUID
    resource: str
    action: str


@dataclass
class RolePermissionAssigned(DomainEvent):
    role_id: UUID
    permission_id: UUID


@dataclass
class RolePermissionRevoked(DomainEvent):
    role_id: UUID
    permission_id: UUID
