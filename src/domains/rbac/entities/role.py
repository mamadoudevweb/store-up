"""Role entity."""
from __future__ import annotations
from uuid import UUID

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.core.entities.base_entity import Entity


@dataclass(kw_only=True)
class Role(Entity[UUID]):
    name: str
    description: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


    @classmethod
    def create(cls, name: str, description: str) -> "Role":
        role = cls(name=name, description=description)

        from src.domains.rbac.events import RoleCreated
        role.register_event(
            RoleCreated(
                role_id=role.id,
                name=role.name
            )
        )

        return role

    
    def update(self, description: str | None = None) -> None:
        if description is not None:
            self.description = description
        self.updated_at = datetime.now(timezone.utc)

        from src.domains.rbac.events import RoleUpdated
        self.register_event(
            RoleUpdated(
                role_id=self.id,
                description=self.description
            )
        )

    def mark_deleted(self) -> None:
        from src.domains.rbac.events import RoleDeleted
        self.register_event(RoleDeleted(role_id=self.id))
