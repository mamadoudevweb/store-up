"""Accounts v1 routes — /api/v1/accounts and /api/v1/accounts/{id}/..."""
from __future__ import annotations

from uuid import UUID

from flask import Blueprint, current_app, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from pydantic import ValidationError

from src.domains.accounts.repositories.base_repository import AccountFilter
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
from src.domains.shared.responses import paginated, success

router = Blueprint("accounts", __name__)


def _get_service():  # type: ignore[no-untyped-def]
    return current_app.extensions["account_service"]


def _serialize_account(account) -> dict:  # type: ignore[no-untyped-def]
    return AccountResponse(
        id=account.id,
        first_name=account.first_name,
        last_name=account.last_name,
        birth_date=account.birth_date,
        status=account.status.value,
        created_at=account.created_at,
        updated_at=account.updated_at,
    ).model_dump(mode="json")


def _serialize_credential(cred) -> dict:  # type: ignore[no-untyped-def]
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
@jwt_required()
def create_account():  # type: ignore[no-untyped-def]
    body = CreateAccountRequest.model_validate(request.get_json(force=True))
    result = _get_service().create_account(
        first_name=body.first_name,
        last_name=body.last_name,
        birth_date=body.birth_date,
    )
    return success(_serialize_account(result.data), status=201)


@router.get("/accounts")
@jwt_required()
def list_accounts():  # type: ignore[no-untyped-def]
    filters = AccountFilter(
        page=int(request.args.get("page", 1)),
        limit=int(request.args.get("limit", 20)),
        search=request.args.get("search"),
        status=request.args.get("status"),
    )
    result = _get_service().list_accounts(filters)
    return paginated(result.data, _serialize_account)


@router.get("/accounts/<uuid:account_id>")
@jwt_required()
def get_account(account_id: UUID):  # type: ignore[no-untyped-def]
    result = _get_service().get_account(account_id)
    return success(_serialize_account(result.data))


@router.put("/accounts/<uuid:account_id>")
@jwt_required()
def update_account(account_id: UUID):  # type: ignore[no-untyped-def]
    body = UpdateAccountRequest.model_validate(request.get_json(force=True))
    result = _get_service().update_account(
        account_id=account_id,
        first_name=body.first_name,
        last_name=body.last_name,
        birth_date=body.birth_date,
    )
    return success(_serialize_account(result.data))


@router.delete("/accounts/<uuid:account_id>")
@jwt_required()
def suspend_account(account_id: UUID):  # type: ignore[no-untyped-def]
    """Soft delete — suspends the account."""
    result = _get_service().suspend_account(account_id)
    return success(_serialize_account(result.data))


# ── Credentials ────────────────────────────────────────────────────────────────

@router.post("/accounts/<uuid:account_id>/credentials")
@jwt_required()
def set_credentials(account_id: UUID):  # type: ignore[no-untyped-def]
    body = SetCredentialsRequest.model_validate(request.get_json(force=True))
    result = _get_service().set_credentials(
        account_id=account_id,
        username=body.username,
        email=str(body.email),
        password=body.password,
    )
    return success(_serialize_credential(result.data), status=201)


@router.get("/accounts/<uuid:account_id>/credentials")
@jwt_required()
def get_credentials(account_id: UUID):  # type: ignore[no-untyped-def]
    result = _get_service().get_credentials(account_id)
    return success(_serialize_credential(result.data))


@router.put("/accounts/<uuid:account_id>/credentials")
@jwt_required()
def update_credentials(account_id: UUID):  # type: ignore[no-untyped-def]
    body = UpdateCredentialsRequest.model_validate(request.get_json(force=True))
    result = _get_service().update_credentials(
        account_id=account_id,
        username=body.username,
        email=str(body.email) if body.email else None,
        password=body.password,
    )
    return success(_serialize_credential(result.data))


# ── Role assignments ───────────────────────────────────────────────────────────

@router.post("/accounts/<uuid:account_id>/roles")
@jwt_required()
def assign_role(account_id: UUID):  # type: ignore[no-untyped-def]
    body = AssignRoleRequest.model_validate(request.get_json(force=True))
    caller_id = UUID(get_jwt_identity())
    result = _get_service().assign_role(
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
    return success(data, status=201)


@router.get("/accounts/<uuid:account_id>/roles")
@jwt_required()
def list_account_roles(account_id: UUID):  # type: ignore[no-untyped-def]
    result = _get_service().list_roles(account_id)
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
    return success(data)


@router.delete("/accounts/<uuid:account_id>/roles/<uuid:role_id>")
@jwt_required()
def revoke_role(account_id: UUID, role_id: UUID):  # type: ignore[no-untyped-def]
    _get_service().revoke_role(account_id, role_id)
    return success(None)
