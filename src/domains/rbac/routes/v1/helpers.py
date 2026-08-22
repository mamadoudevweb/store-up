"""RBAC route helpers."""
from __future__ import annotations
from typing import Any

from flask import current_app

from src.domains.rbac.routes.v1.schemas.rbac_schemas import (
    PermissionResponse,
    RoleResponse,
)
from src.core.routes.envelope import ok, EnvelopeResponse


def get_rbac_service() -> Any:
    """Retrieve the RbacService from the current app context."""
    return current_app.extensions["domain_service"].rbac


def serialize_role(role) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    """Serialize a Role entity."""
    return RoleResponse.model_validate(role).model_dump(mode="json")


def serialize_permission(perm) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    """Serialize a Permission entity."""
    return PermissionResponse.model_validate(perm).model_dump(mode="json")


def paginated(result: Any, serializer: Any) -> EnvelopeResponse:
    """Helper to return paginated core EnvelopeResponse."""
    return ok(
        data=[serializer(item) for item in result.items],
        meta={"page": result.page, "limit": result.limit, "total": result.total}
    )
