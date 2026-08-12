"""Pydantic schemas for the RBAC domain routes."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Request schemas ────────────────────────────────────────────────────────────

class CreateRoleRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(None, max_length=255)


class UpdateRoleRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    description: str | None = Field(None, max_length=255)


class CreatePermissionRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    resource: str = Field(min_length=1, max_length=100)
    action: str = Field(min_length=1, max_length=100)
    description: str | None = Field(None, max_length=255)


class AssignPermissionRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    permission_id: UUID


# ── Response schemas ───────────────────────────────────────────────────────────

class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resource: str
    action: str
    name: str
    description: str | None
    created_at: datetime
