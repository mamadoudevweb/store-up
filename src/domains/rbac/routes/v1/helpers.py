"""RBAC route helpers."""
from __future__ import annotations

from flask import current_app

from src.domains.rbac.routes.v1.schemas.rbac_schemas import (
    PermissionResponse,
    RoleResponse,
)


def get_rbac_service():  # type: ignore[no-untyped-def]
    """Retrieve the RbacService from the current app context."""
    return current_app.extensions["rbac_service"]


def serialize_role(role) -> dict:  # type: ignore[no-untyped-def]
    """Serialize a Role entity."""
    return RoleResponse.model_validate(role).model_dump(mode="json")


def serialize_permission(perm) -> dict:  # type: ignore[no-untyped-def]
    """Serialize a Permission entity."""
    return PermissionResponse.model_validate(perm).model_dump(mode="json")
