"""Mappers between Account ORM models and domain entities."""
from __future__ import annotations

from src.core.repositories.utils import Mapper
from src.domains.accounts.entities import Account, AccountRole, AccountStatus, Credential
from src.domains.accounts.repositories.sql.orms import (
    AccountModel,
    AccountRoleModel,
    CredentialModel,
)

class AccountMapper(Mapper[Account, AccountModel]):
    def to_entity(self, model: AccountModel) -> Account:
        return Account(
            id=model.id,
            first_name=model.first_name,
            last_name=model.last_name,
            birth_date=model.birth_date,
            status=AccountStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def to_model(self, entity: Account, model: AccountModel | None = None) -> AccountModel:
        model = model or AccountModel()
        if entity.id is not None:
            model.id = entity.id
        model.first_name = entity.first_name
        model.last_name = entity.last_name
        model.birth_date = entity.birth_date
        model.status = entity.status.value
        model.created_at = entity.created_at
        model.updated_at = entity.updated_at
        return model

class CredentialMapper(Mapper[Credential, CredentialModel]):
    def to_entity(self, model: CredentialModel) -> Credential:
        return Credential(
            id=model.id,
            account_id=model.account_id,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash,
            last_login_at=model.last_login_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def to_model(self, entity: Credential, model: CredentialModel | None = None) -> CredentialModel:
        model = model or CredentialModel()
        if entity.id is not None:
            model.id = entity.id
        model.account_id = entity.account_id
        model.username = entity.username
        model.email = entity.email
        model.password_hash = entity.password_hash
        model.last_login_at = entity.last_login_at
        model.created_at = entity.created_at
        model.updated_at = entity.updated_at
        return model

class AccountRoleMapper(Mapper[AccountRole, AccountRoleModel]):
    def to_entity(self, model: AccountRoleModel) -> AccountRole:
        return AccountRole(
            account_id=model.account_id,
            role_id=model.role_id,
            domain_scope=model.domain_scope,
            assigned_at=model.assigned_at,
            assigned_by=model.assigned_by,
        )

    def to_model(self, entity: AccountRole, model: AccountRoleModel | None = None) -> AccountRoleModel:
        model = model or AccountRoleModel()
        model.account_id = entity.account_id
        model.role_id = entity.role_id
        model.domain_scope = entity.domain_scope
        model.assigned_at = entity.assigned_at
        model.assigned_by = entity.assigned_by
        return model
