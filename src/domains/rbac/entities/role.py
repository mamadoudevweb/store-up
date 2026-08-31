"""Role entity."""
from __future__ import annotations
from uuid import UUID

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.core.entities.base_entity import Entity
from src.domains.rbac.events import RoleCreated, RoleUpdated, RoleDeleted


@dataclass(kw_only=True)
class Role(Entity[UUID]):
    name: str
    description: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


    @classmethod
    def create(cls, name: str, description: str) -> "Role":
        role = cls(id=uuid.uuid4(), name=name, description=description)

        if role.id is None:
            raise ValueError("role ID cannot be None")
        role.register_event(
            RoleCreated(
                role_id=role.id,
                name=role.name
            )
        )

        return role

    
    def update(self, description: str | None = None) -> None:
        if self.id is None:
            raise ValueError("self ID cannot be None")
        if description is not None:
            self.description = description
        self.updated_at = datetime.now(timezone.utc)

        self.register_event(
            RoleUpdated(
                role_id=self.id,
                description=self.description or ""
            )
        )

    def mark_deleted(self) -> None:
        if self.id is None:
            raise ValueError("self ID cannot be None")
        self.register_event(RoleDeleted(role_id=self.id, name=self.name))
