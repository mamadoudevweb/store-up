"""RolePermission entity — represents a role-permission assignment."""
from __future__ import annotations
from uuid import UUID

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.core.entities.base_entity import Entity
from src.domains.rbac.events import RolePermissionAssigned, RolePermissionRevoked

@dataclass(kw_only=True)
class RolePermission(Entity[UUID]):
    role_id: uuid.UUID
    permission_id: uuid.UUID
    assigned_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    revoked_at: datetime | None = None

    @property
    def active(self) -> bool:
        return self.revoked_at is None

    
    @classmethod
    def assign_permission(cls, role_id: uuid.UUID, permission_id: uuid.UUID) -> "RolePermission":
        role_permission = cls(
            id=uuid.uuid4(),
            role_id=role_id,
            permission_id=permission_id
        )

        role_permission.register_event(
            RolePermissionAssigned(
                role_id=role_permission.role_id,
                permission_id=role_permission.permission_id
            )
        )

        return role_permission
        

    def revoke_permission(self) -> None:
        self.revoked_at = datetime.now(timezone.utc)
        self.register_event(
            RolePermissionRevoked(
                role_id=self.role_id,
                permission_id=self.permission_id
            )
        )

    def reactivate(self) -> None:
        self.revoked_at = None
        self.assigned_at = datetime.now(timezone.utc)
        self.register_event(
            RolePermissionAssigned(
                role_id=self.role_id,
                permission_id=self.permission_id
            )
        )
