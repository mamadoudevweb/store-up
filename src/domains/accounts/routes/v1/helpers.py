"""Route helpers for accounts domain."""
from __future__ import annotations

from flask import current_app

from src.domains.accounts.routes.v1.schemas.account_schemas import (
    AccountResponse,
    AccountRoleResponse,
    CredentialResponse,
)


def get_account_service():  # type: ignore[no-untyped-def]
    return current_app.extensions["account_service"]


def serialize_account(account) -> dict:  # type: ignore[no-untyped-def]
    return AccountResponse.model_validate(account).model_dump(mode="json")


def serialize_credential(cred) -> dict:  # type: ignore[no-untyped-def]
    return CredentialResponse.model_validate(cred).model_dump(mode="json")


def serialize_account_role(role) -> dict:  # type: ignore[no-untyped-def]
    return AccountRoleResponse.model_validate(role).model_dump(mode="json")
