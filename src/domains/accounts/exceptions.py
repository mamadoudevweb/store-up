"""Accounts domain exceptions — scoped to this domain only."""
from __future__ import annotations

from http import HTTPStatus

from src.core.services.errors import AppError


class AccountNotFound(AppError):
    code = "ACCOUNT_NOT_FOUND"
    http_status = HTTPStatus.NOT_FOUND
    message = "Account not found"


class AccountSuspendedError(AppError):
    code = "ACCOUNT_SUSPENDED"
    http_status = HTTPStatus.FORBIDDEN
    message = "Account is suspended"


class CredentialNotFound(AppError):
    code = "CREDENTIAL_NOT_FOUND"
    http_status = HTTPStatus.NOT_FOUND
    message = "Credentials not found for this account"


class CredentialAlreadyExists(AppError):
    code = "CREDENTIAL_ALREADY_EXISTS"
    http_status = HTTPStatus.CONFLICT
    message = "Credentials already set for this account"


class UsernameConflict(AppError):
    code = "USERNAME_CONFLICT"
    http_status = HTTPStatus.CONFLICT
    message = "Username is already taken"


class EmailConflict(AppError):
    code = "EMAIL_CONFLICT"
    http_status = HTTPStatus.CONFLICT
    message = "Email is already in use"


class RoleAlreadyAssigned(AppError):
    code = "ROLE_ALREADY_ASSIGNED"
    http_status = HTTPStatus.CONFLICT
    message = "This role is already assigned to the account"


class RoleAssignmentNotFound(AppError):
    code = "ROLE_ASSIGNMENT_NOT_FOUND"
    http_status = HTTPStatus.NOT_FOUND
    message = "Role assignment not found"
