"""Permission entity."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Permission:
    resource: str      # e.g., 'products', 'accounts'
    action: str        # e.g., 'read', 'write', 'delete'
    description: str | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def name(self) -> str:
        """Convenience property for string representation, e.g., 'products:read'."""
        return f"{self.resource}:{self.action}"
