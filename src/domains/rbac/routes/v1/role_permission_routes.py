"""Role-Permission assignment routes."""
from __future__ import annotations

from uuid import UUID

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from src.domains.rbac.routes.v1.helpers import get_rbac_service, serialize_permission
from src.domains.rbac.routes.v1.schemas.rbac_schemas import AssignPermissionRequest
from src.domains.shared.responses import paginated, success

bp = Blueprint("role_permission", __name__)


@bp.post("/<uuid:role_id>/permissions")
@jwt_required()
def assign_permission(role_id: UUID):  # type: ignore[no-untyped-def]
    body = AssignPermissionRequest.model_validate(request.get_json(force=True))
    result = get_rbac_service().role_permission.assign(role_id, body.permission_id)
    return success(None, status=201)


@bp.get("/<uuid:role_id>/permissions")
@jwt_required()
def list_role_permissions(role_id: UUID):  # type: ignore[no-untyped-def]
    result = get_rbac_service().permission.list_role_permissions(role_id)
    return paginated(result.data, serialize_permission)


@bp.delete("/<uuid:role_id>/permissions/<uuid:permission_id>")
@jwt_required()
def revoke_permission(role_id: UUID, permission_id: UUID):  # type: ignore[no-untyped-def]
    get_rbac_service().role_permission.revoke(role_id, permission_id)
    return success(None)
