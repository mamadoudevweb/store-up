"""RBAC repository filters."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.domains.shared.filters import BaseFilter


@dataclass
class RoleFilter(BaseFilter):
    id: uuid.UUID | None = None
    name: str | None = None


@dataclass
class PermissionFilter(BaseFilter):
    id: uuid.UUID | None = None
    resource: str | None = None
    action: str | None = None
    role_id: uuid.UUID | None = None


@dataclass
class RolePermissionFilter(BaseFilter):
    role_id: uuid.UUID | None = None
    permission_id: uuid.UUID | None = None

