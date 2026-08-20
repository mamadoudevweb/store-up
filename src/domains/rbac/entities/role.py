"""Role entity."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from src.core.entities.base_entity import Entity


@dataclass(kw_only=True)
class Role(Entity):
    name: str
    description: str | None = None

    def update(self, description: str | None = None) -> None:
        if description is not None:
            self.description = description
        self.updated_at = datetime.now(timezone.utc)
