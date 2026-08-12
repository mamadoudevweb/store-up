"""Permission routes."""
from __future__ import annotations

from uuid import UUID

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from src.domains.rbac.repositories.filters import PermissionFilter
from src.domains.rbac.routes.v1.helpers import get_rbac_service, serialize_permission
from src.domains.rbac.routes.v1.schemas.rbac_schemas import CreatePermissionRequest
from src.domains.shared.responses import paginated, success

bp = Blueprint("permission", __name__)


@bp.post("")
@jwt_required()
def create_permission():  # type: ignore[no-untyped-def]
    body = CreatePermissionRequest.model_validate(request.get_json(force=True))
    result = get_rbac_service().permission.create_permission(
        resource=body.resource,
        action=body.action,
        description=body.description,
    )
    return success(serialize_permission(result.data), status=201)


@bp.get("")
@jwt_required()
def list_permissions():  # type: ignore[no-untyped-def]
    filters = PermissionFilter(
        page=int(request.args.get("page", 1)),
        limit=int(request.args.get("limit", 20)),
        resource=request.args.get("resource"),
        action=request.args.get("action"),
    )
    with get_rbac_service()._uow as uow:
        result = uow.permissions.list(filters)
    return paginated(result, serialize_permission)


@bp.get("/<uuid:permission_id>")
@jwt_required()
def get_permission(permission_id: UUID):  # type: ignore[no-untyped-def]
    result = get_rbac_service().permission.get_permission(permission_id)
    return success(serialize_permission(result.data))


@bp.delete("/<uuid:permission_id>")
@jwt_required()
def delete_permission(permission_id: UUID):  # type: ignore[no-untyped-def]
    svc = get_rbac_service()
    with svc._uow as uow:
        perm = uow.permissions.get(PermissionFilter(id=permission_id))
        if perm:
            uow.permissions.delete(perm)
            uow.commit()
    return success(None)
