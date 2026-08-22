"""Accounts v1 routes — /api/v1/accounts and /api/v1/accounts/{id}/..."""
from __future__ import annotations

from uuid import UUID

from flask import Blueprint, current_app, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.app.identity import get_current_actor
from src.domains.accounts.repositories.filters import AccountFilter
from src.domains.accounts.routes.v1.schemas.account_schemas import (
    AccountResponse,
    AccountRoleResponse,
    AssignRoleRequest,
    CreateAccountRequest,
    CredentialResponse,
    SetCredentialsRequest,
    UpdateAccountRequest,
    UpdateCredentialsRequest,
)
from src.core.routes.envelope import ok

router = Blueprint("accounts", __name__)


from typing import Any

def _get_domain_service():
    return current_app.extensions["domain_service"]


def _serialize_account(account) -> dict[str, Any]:
    return AccountResponse(
        id=account.id,
        first_name=account.first_name,
        last_name=account.last_name,
        birth_date=account.birth_date,
        status=account.status.value,
        created_at=account.created_at,
        updated_at=account.updated_at,
    ).model_dump(mode="json")


def _serialize_credential(cred) -> dict[str, Any]:
    return CredentialResponse(
        id=cred.id,
        account_id=cred.account_id,
        username=cred.username,
        email=cred.email,
        last_login_at=cred.last_login_at,
        created_at=cred.created_at,
        updated_at=cred.updated_at,
    ).model_dump(mode="json")


# ── Accounts ───────────────────────────────────────────────────────────────────

@router.post("/accounts")
# Registration route might not need @jwt_required depending on whether registration is open
def create_account():
    body = CreateAccountRequest.model_validate(request.get_json(force=True))
    result = _get_domain_service().accounts.account.create_account(
        first_name=body.first_name,
        last_name=body.last_name,
        birth_date=body.birth_date,
    )
    return ok(_serialize_account(result.data), status=201)


@router.get("/accounts")
@jwt_required()
def list_accounts():
    actor = get_current_actor()
    filters = AccountFilter(
        page=int(request.args.get("page", 1)),
        limit=int(request.args.get("limit", 20)),
        search=request.args.get("search"),
        status=request.args.get("status"),
    )
    result = _get_domain_service().accounts.account.list_accounts(actor, filters)
    data = [_serialize_account(acc) for acc in result.data.items]
    meta = {
        "page": result.data.page,
        "limit": result.data.limit,
        "total": result.data.total,
        "total_pages": result.data.total_pages,
    }
    return ok(data=data, meta=meta)


@router.get("/accounts/<uuid:account_id>")
@jwt_required()
def get_account(account_id: UUID):
    actor = get_current_actor()
    result = _get_domain_service().accounts.account.get_account(actor, account_id)
    return ok(_serialize_account(result.data))


@router.put("/accounts/<uuid:account_id>")
@jwt_required()
def update_account(account_id: UUID):
    actor = get_current_actor()
    body = UpdateAccountRequest.model_validate(request.get_json(force=True))
    result = _get_domain_service().accounts.account.update_account(
        actor=actor,
        account_id=account_id,
        first_name=body.first_name,
        last_name=body.last_name,
        birth_date=body.birth_date,
    )
    return ok(_serialize_account(result.data))


@router.delete("/accounts/<uuid:account_id>")
@jwt_required()
def suspend_account(account_id: UUID):
    actor = get_current_actor()
    """Soft delete — suspends the account."""
    result = _get_domain_service().accounts.account.suspend_account(actor, account_id)
    return ok(_serialize_account(result.data))


# ── Credentials ────────────────────────────────────────────────────────────────

@router.post("/accounts/<uuid:account_id>/credentials")
def set_credentials(account_id: UUID):
    # This might not need actor if setting initial credentials during registration
    body = SetCredentialsRequest.model_validate(request.get_json(force=True))
    result = _get_domain_service().accounts.credential.set_credentials(
        account_id=account_id,
        username=body.username,
        email=str(body.email),
        password=body.password,
    )
    return ok(_serialize_credential(result.data), status=201)


@router.get("/accounts/<uuid:account_id>/credentials")
@jwt_required()
def get_credentials(account_id: UUID):
    actor = get_current_actor()
    result = _get_domain_service().accounts.credential.get_credentials(actor, account_id)
    return ok(_serialize_credential(result.data))


@router.put("/accounts/<uuid:account_id>/credentials")
@jwt_required()
def update_credentials(account_id: UUID):
    actor = get_current_actor()
    body = UpdateCredentialsRequest.model_validate(request.get_json(force=True))
    result = _get_domain_service().accounts.credential.update_credentials(
        actor=actor,
        account_id=account_id,
        username=body.username,
        email=str(body.email) if body.email else None,
        password=body.password,
    )
    return ok(_serialize_credential(result.data))


# ── Role assignments ───────────────────────────────────────────────────────────

@router.post("/accounts/<uuid:account_id>/roles")
@jwt_required()
def assign_role(account_id: UUID):
    actor = get_current_actor()
    body = AssignRoleRequest.model_validate(request.get_json(force=True))
    caller_id = UUID(get_jwt_identity())
    result = _get_domain_service().accounts.account_role.assign_role(
        actor=actor,
        account_id=account_id,
        role_id=body.role_id,
        assigned_by=caller_id,
        domain_scope=body.domain_scope,
    )
    data = AccountRoleResponse(
        account_id=result.data.account_id,
        role_id=result.data.role_id,
        domain_scope=result.data.domain_scope,
        assigned_at=result.data.assigned_at,
        assigned_by=result.data.assigned_by,
    ).model_dump(mode="json")
    return ok(data, status=201)


@router.get("/accounts/<uuid:account_id>/roles")
@jwt_required()
def list_account_roles(account_id: UUID):
    actor = get_current_actor()
    result = _get_domain_service().accounts.account_role.list_roles(actor, account_id)
    data = [
        AccountRoleResponse(
            account_id=r.account_id,
            role_id=r.role_id,
            domain_scope=r.domain_scope,
            assigned_at=r.assigned_at,
            assigned_by=r.assigned_by,
        ).model_dump(mode="json")
        for r in result.data
    ]
    return ok(data)


@router.delete("/accounts/<uuid:account_id>/roles/<uuid:role_id>")
@jwt_required()
def revoke_role(account_id: UUID, role_id: UUID):
    actor = get_current_actor()
    _get_domain_service().accounts.account_role.revoke_role(actor, account_id, role_id)
    return ok(None)
