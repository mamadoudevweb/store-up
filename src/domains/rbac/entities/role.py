"""Role entity."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Role:
    name: str
    description: str | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def update(self, description: str | None = None) -> None:
        if description is not None:
            self.description = description
        self.updated_at = datetime.now(timezone.utc)
