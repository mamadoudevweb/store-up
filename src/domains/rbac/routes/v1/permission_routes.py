"""Permission routes."""
from __future__ import annotations

from uuid import UUID

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from src.app.identity import get_current_actor
from src.domains.rbac.repositories.filters import PermissionFilter
from src.domains.rbac.routes.v1.helpers import get_rbac_service, serialize_permission, paginated
from src.domains.rbac.routes.v1.schemas.rbac_schemas import CreatePermissionRequest
from src.core.routes.envelope import ok, EnvelopeResponse

bp = Blueprint("permission", __name__)


@bp.post("")
@jwt_required()
def create_permission() -> EnvelopeResponse:
    actor = get_current_actor()
    body = CreatePermissionRequest.model_validate(request.get_json(force=True))
    result = get_rbac_service().permission.create_permission(
        actor=actor,
        resource=body.resource,
        action=body.action,
        description=body.description,
    )
    return ok(serialize_permission(result.data), status=201)


@bp.get("")
@jwt_required()
def list_permissions() -> EnvelopeResponse:
    actor = get_current_actor()
    get_rbac_service().permission._authorize(actor, "rbac", "permission", "list")
    filters = PermissionFilter(
        page=int(request.args.get("page", 1)),
        limit=int(request.args.get("limit", 20)),
        resource=request.args.get("resource"),
        action=request.args.get("action"),
    )
    with get_rbac_service()._uow_factory() as uow:
        result = uow.permissions.list(filters)
    return paginated(result, serialize_permission)


@bp.get("/<uuid:permission_id>")
@jwt_required()
def get_permission(permission_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    result = get_rbac_service().permission.get_permission(actor, permission_id)
    return ok(serialize_permission(result.data))


@bp.delete("/<uuid:permission_id>")
@jwt_required()
def delete_permission(permission_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    svc = get_rbac_service()
    svc.permission.delete_permission(actor, permission_id)
    return ok(None)
