"""Pydantic schemas for the accounts domain routes."""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Request schemas ────────────────────────────────────────────────────────────

class CreateAccountRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    birth_date: date | None = None


class UpdateAccountRequest(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    birth_date: date | None = None


class SetCredentialsRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UpdateCredentialsRequest(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=100)
    email: EmailStr | None = None
    password: str | None = Field(None, min_length=8, max_length=128)


class AssignRoleRequest(BaseModel):
    role_id: UUID
    domain_scope: str | None = None


# ── Response schemas ───────────────────────────────────────────────────────────

class AccountResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    birth_date: date | None
    status: str
    created_at: datetime
    updated_at: datetime


class CredentialResponse(BaseModel):
    id: UUID
    account_id: UUID
    username: str
    email: str
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
    # NOTE: password_hash is NEVER included


class AccountRoleResponse(BaseModel):
    account_id: UUID
    role_id: UUID
    domain_scope: str | None
    assigned_at: datetime
    assigned_by: UUID | None
