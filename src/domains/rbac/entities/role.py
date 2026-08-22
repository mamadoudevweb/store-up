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

    def update(self, description: str | None = None) -> None:
        if description is not None:
            self.description = description
        self.updated_at = datetime.now(timezone.utc)
