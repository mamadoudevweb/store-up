"""RBAC repository filters."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.core.entities.pagination import EntityFilter


@dataclass(kw_only=True)
class RoleFilter(EntityFilter):
    id: uuid.UUID | None = None
    name: str | None = None


@dataclass(kw_only=True)
class PermissionFilter(EntityFilter):
    id: uuid.UUID | None = None
    resource: str | None = None
    action: str | None = None
    role_id: uuid.UUID | None = None


@dataclass(kw_only=True)
class RolePermissionFilter(EntityFilter):
    role_id: uuid.UUID | None = None
    permission_id: uuid.UUID | None = None

