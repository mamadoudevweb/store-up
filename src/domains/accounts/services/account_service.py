"""Account service — business logic for Account and Credential management."""
from __future__ import annotations

from datetime import date
from uuid import UUID

import bcrypt

from src.domains.accounts.entities import Account, AccountRole, Credential
from src.domains.accounts.exceptions import (
    AccountNotFound,
    AccountSuspendedError,
    CredentialAlreadyExists,
    CredentialNotFound,
    EmailConflict,
    RoleAlreadyAssigned,
    RoleAssignmentNotFound,
    UsernameConflict,
)
from src.domains.accounts.events import RoleAssigned, RoleRevoked
from src.domains.accounts.repositories.filters import (
    AccountFilter,
    AccountRoleFilter,
    CredentialFilter,
)
from src.domains.accounts.repositories.base_uow import BaseAccountUnitOfWork
from src.domains.shared.events import EventBus
from src.domains.shared.pagination import Paginated
from src.domains.shared.service_result import ServiceResult


class AccountService:
    """All account + credential business operations."""

    def __init__(self, uow: BaseAccountUnitOfWork, event_bus: EventBus) -> None:
        self._uow = uow
        self._bus = event_bus

    # ── Account CRUD ───────────────────────────────────────────────────────

    def create_account(
        self,
        first_name: str,
        last_name: str,
        birth_date: date | None = None,
    ) -> ServiceResult[Account]:
        account = Account.create(first_name, last_name, birth_date)
        with self._uow as uow:
            uow.accounts.add(account)
            uow.commit()
        self._bus.publish_all(account.pull_events())
        return ServiceResult.ok(account)

    def get_account(self, account_id: UUID) -> ServiceResult[Account]:
        with self._uow as uow:
            account = uow.accounts.get(AccountFilter(id=account_id))
        if not account:
            raise AccountNotFound()
        return ServiceResult.ok(account)

    def list_accounts(self, filters: AccountFilter) -> ServiceResult[Paginated[Account]]:
        with self._uow as uow:
            result = uow.accounts.list(filters)
        return ServiceResult.ok(result)

    def update_account(
        self,
        account_id: UUID,
        first_name: str | None = None,
        last_name: str | None = None,
        birth_date: date | None = None,
    ) -> ServiceResult[Account]:
        with self._uow as uow:
            account = uow.accounts.get(AccountFilter(id=account_id))
            if not account:
                raise AccountNotFound()
            account.update(first_name, last_name, birth_date)
            uow.accounts.update(account)
            uow.commit()
        self._bus.publish_all(account.pull_events())
        return ServiceResult.ok(account)

    def suspend_account(self, account_id: UUID) -> ServiceResult[Account]:
        with self._uow as uow:
            account = uow.accounts.get(AccountFilter(id=account_id))
            if not account:
                raise AccountNotFound()
            account.suspend()
            uow.accounts.update(account)
            uow.commit()
        self._bus.publish_all(account.pull_events())
        return ServiceResult.ok(account)

    # ── Credential management ──────────────────────────────────────────────

    def set_credentials(
        self,
        account_id: UUID,
        username: str,
        email: str,
        password: str,
    ) -> ServiceResult[Credential]:
        with self._uow as uow:
            account = uow.accounts.get(AccountFilter(id=account_id))
            if not account:
                raise AccountNotFound()
            if not account.is_active():
                raise AccountSuspendedError()
                
            if uow.credentials.exists(CredentialFilter(account_id=account_id)):
                raise CredentialAlreadyExists()
                
            if uow.credentials.exists(CredentialFilter(username=username)):
                raise UsernameConflict()
                
            if uow.credentials.exists(CredentialFilter(email=email)):
                raise EmailConflict()
                
            password_hash = bcrypt.hashpw(
                password.encode(), bcrypt.gensalt()
            ).decode()
            cred = Credential.create(account_id, username, email, password_hash)
            uow.credentials.add(cred)
            uow.commit()
        self._bus.publish_all(cred.pull_events())
        return ServiceResult.ok(cred)

    def get_credentials(self, account_id: UUID) -> ServiceResult[Credential]:
        with self._uow as uow:
            cred = uow.credentials.get(CredentialFilter(account_id=account_id))
        if not cred:
            raise CredentialNotFound()
        return ServiceResult.ok(cred)

    def update_credentials(
        self,
        account_id: UUID,
        username: str | None = None,
        email: str | None = None,
        password: str | None = None,
    ) -> ServiceResult[Credential]:
        with self._uow as uow:
            cred = uow.credentials.get(CredentialFilter(account_id=account_id))
            if not cred:
                raise CredentialNotFound()
            
            if username and username != cred.username:
                if uow.credentials.exists(CredentialFilter(username=username)):
                    raise UsernameConflict()
            if email and email != cred.email:
                if uow.credentials.exists(CredentialFilter(email=email)):
                    raise EmailConflict()
                    
            password_hash: str | None = None
            if password:
                password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            cred.update(username, email, password_hash)
            uow.credentials.update(cred)
            uow.commit()
        self._bus.publish_all(cred.pull_events())
        return ServiceResult.ok(cred)

    # ── Role assignment ────────────────────────────────────────────────────

    def assign_role(
        self,
        account_id: UUID,
        role_id: UUID,
        assigned_by: UUID | None = None,
        domain_scope: str | None = None,
    ) -> ServiceResult[AccountRole]:
        with self._uow as uow:
            account = uow.accounts.get(AccountFilter(id=account_id))
            if not account:
                raise AccountNotFound()
            
            if uow.account_roles.exists(AccountRoleFilter(account_id=account_id, role_id=role_id)):
                raise RoleAlreadyAssigned()
            assignment = AccountRole.create(account_id, role_id, assigned_by, domain_scope)
            uow.account_roles.add(assignment)
            uow.commit()
        self._bus.publish(RoleAssigned(
            account_id=account_id, role_id=role_id, domain_scope=domain_scope
        ))
        return ServiceResult.ok(assignment)

    def list_roles(self, account_id: UUID) -> ServiceResult[list[AccountRole]]:
        with self._uow as uow:
            account = uow.accounts.get(AccountFilter(id=account_id))
            if not account:
                raise AccountNotFound()
            # Still use list here because an account can have multiple roles
            roles = uow.account_roles.list(AccountRoleFilter(account_id=account_id, limit=100)).items
        return ServiceResult.ok(roles)

    def revoke_role(self, account_id: UUID, role_id: UUID) -> ServiceResult[None]:
        with self._uow as uow:
            assignment = uow.account_roles.get(AccountRoleFilter(account_id=account_id, role_id=role_id))
            if not assignment:
                raise RoleAssignmentNotFound()
            uow.account_roles.delete(assignment)
            uow.commit()
        self._bus.publish(RoleRevoked(account_id=account_id, role_id=role_id))
        return ServiceResult.ok(None)

    def get_effective_permissions(self, account_id: UUID) -> ServiceResult[list[str]]:
        """Resolved union of all permissions across all of the account's roles."""
        with self._uow as uow:
            account = uow.accounts.get(AccountFilter(id=account_id))
            if not account:
                raise AccountNotFound()
            role_assignments = uow.account_roles.list(AccountRoleFilter(account_id=account_id, limit=100)).items
        # Permission resolution is delegated to the RBAC domain service
        return ServiceResult.ok([str(r.role_id) for r in role_assignments])
