"""Permission entity."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.core.entities.base_entity import Entity


@dataclass(kw_only=True)
class Permission(Entity):
    resource: str
    action: str
    description: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    
    @classmethod
    def create(cls, resource: str, action: str, description: str) -> "Permission":
        ...
        # :TODO: implement later

    # Permission can't be updated or deleted and is created at application boot time
    
    @property
    def name(self) -> str:
        """Convenience property for string representation, e.g., 'products:read'."""
        return f"{self.resource}:{self.action}"
