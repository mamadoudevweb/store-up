"""RolePermission entity — represents a role-permission assignment."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.core.entities.base_entity import Entity

@dataclass(kw_only=True)
class RolePermission(Entity):
    role_id: uuid.UUID
    permission_id: uuid.UUID
    assigned_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    revoked_at: datetime = field(default_factory=lambda: datetime.now(timezon.utc))

    
    @classmethod
    def assign_permission(cls, role_id: uuid.UUID, permission_id: uuid.UUID) -> "RolePermission":
        role_permission = cls(
            role_id=role_id,
            permission_id=permission_id
        )

        from src.domains.rbac.events import RolePermissionAssigned
        role_permission.register_event(
            RolePermissionAssigned(
                role_id=role_id,
                permission_id=permission_id
            )
        )

        return role_permission
        

    # :TODO: Implement rovoke permission method
    
