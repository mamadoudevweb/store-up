"""Role routes."""
from __future__ import annotations

from uuid import UUID

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from src.app.identity import get_current_actor
from src.domains.rbac.repositories.filters import RoleFilter
from src.domains.rbac.routes.v1.helpers import get_rbac_service, serialize_role, paginated
from src.domains.rbac.routes.v1.schemas.rbac_schemas import CreateRoleRequest
from src.core.routes.envelope import ok

bp = Blueprint("role", __name__)


@bp.post("")
@jwt_required()
def create_role():  # type: ignore[no-untyped-def]
    actor = get_current_actor()
    body = CreateRoleRequest.model_validate(request.get_json(force=True))
    result = get_rbac_service().role.create_role(
        actor=actor,
        name=body.name,
        description=body.description,
    )
    return ok(serialize_role(result.data), status=201)


@bp.get("")
@jwt_required()
def list_roles():  # type: ignore[no-untyped-def]
    actor = get_current_actor()
    # Need to authorize list? Wait, list is done via uow directly here.
    # Let's call the service if we want to authorize it, or just authorize here.
    get_rbac_service().role._authorize(actor, "rbac", "role", "list")
    filters = RoleFilter(
        page=int(request.args.get("page", 1)),
        limit=int(request.args.get("limit", 20)),
        name=request.args.get("name"),
    )
    with get_rbac_service()._uow_factory() as uow:
        result = uow.roles.list(filters)
    return paginated(result, serialize_role)


@bp.get("/<uuid:role_id>")
@jwt_required()
def get_role(role_id: UUID):  # type: ignore[no-untyped-def]
    actor = get_current_actor()
    result = get_rbac_service().role.get_role(actor, role_id)
    return ok(serialize_role(result.data))


@bp.delete("/<uuid:role_id>")
@jwt_required()
def delete_role(role_id: UUID):  # type: ignore[no-untyped-def]
    actor = get_current_actor()
    svc = get_rbac_service()
    svc.role.delete_role(actor, role_id)
    return ok(None)
