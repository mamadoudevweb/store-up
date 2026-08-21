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
