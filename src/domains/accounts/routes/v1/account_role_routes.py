"""AccountRole entity routes."""
from __future__ import annotations

from uuid import UUID

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.domains.accounts.routes.v1.helpers import (
    get_account_service,
    serialize_account_role,
)
from src.domains.accounts.routes.v1.schemas.account_schemas import AssignRoleRequest
from src.domains.shared.responses import success

bp = Blueprint("account_role", __name__)


@bp.post("/<uuid:account_id>/roles")
@jwt_required()
def assign_role(account_id: UUID):  # type: ignore[no-untyped-def]
    body = AssignRoleRequest.model_validate(request.get_json(force=True))
    caller_id = UUID(get_jwt_identity())
    result = get_account_service().role.assign_role(
        account_id=account_id,
        role_id=body.role_id,
        assigned_by=caller_id,
        domain_scope=body.domain_scope,
    )
    return success(serialize_account_role(result.data), status=201)


@bp.get("/<uuid:account_id>/roles")
@jwt_required()
def list_account_roles(account_id: UUID):  # type: ignore[no-untyped-def]
    result = get_account_service().role.list_roles(account_id)
    return success([serialize_account_role(r) for r in result.data])


@bp.delete("/<uuid:account_id>/roles/<uuid:role_id>")
@jwt_required()
def revoke_role(account_id: UUID, role_id: UUID):  # type: ignore[no-untyped-def]
    get_account_service().role.revoke_role(account_id, role_id)
    return success(None)
