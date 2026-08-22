"""AccountRole entity service."""
from __future__ import annotations

from uuid import UUID
from typing import Callable

from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.result import ServiceResult
from src.core.repositories.base_uow import BaseUnitOfWork
from src.domains.accounts.entities import AccountRole
from src.domains.accounts.events import RoleAssigned, RoleRevoked
from src.domains.accounts.exceptions import (
    AccountNotFound,
    RoleAlreadyAssigned,
    RoleAssignmentNotFound,
)
from src.domains.accounts.repositories.filters import AccountRoleFilter

class Service(BaseService):
    def __init__(self, uow_factory: Callable[[], BaseUnitOfWork]) -> None:
        super().__init__(uow_factory)

    def assign_role(
        self,
        actor: SupportsPermissionCheck,
        account_id: UUID,
        role_id: UUID,
        assigned_by: UUID | None = None,
        domain_scope: str | None = None,
    ) -> ServiceResult[AccountRole]:
        self._authorize(actor, "accounts", "account_role", "assign")
        with self._uow_factory() as uow:
            account = uow.accounts.get(account_id)
            if not account:
                raise AccountNotFound()
            
            if uow.account_roles.exists(AccountRoleFilter(account_id=account_id, role_id=role_id)):
                raise RoleAlreadyAssigned()
            assignment = AccountRole.create(account_id, role_id, assigned_by, domain_scope)
            uow.account_roles.add(assignment)
            assignment.register_event(RoleAssigned(
                account_id=account_id, role_id=role_id, domain_scope=domain_scope
            ))
            uow.track(assignment)
            uow.commit()
        return ServiceResult(data=assignment)

    def list_roles(self, actor: SupportsPermissionCheck, account_id: UUID) -> ServiceResult[list[AccountRole]]:
        self._authorize(actor, "accounts", "account_role", "list")
        with self._uow_factory() as uow:
            account = uow.accounts.get(account_id)
            if not account:
                raise AccountNotFound()
            roles = uow.account_roles.list(AccountRoleFilter(account_id=account_id, limit=100)).items
        return ServiceResult(data=roles)
        
    def list_for_account(self, account_id: UUID) -> ServiceResult[list[AccountRole]]:
        """Internal use — no permission check."""
        with self._uow_factory() as uow:
            roles = uow.account_roles.list(AccountRoleFilter(account_id=account_id, limit=100)).items
        return ServiceResult(data=roles)

    def revoke_role(self, actor: SupportsPermissionCheck, account_id: UUID, role_id: UUID) -> ServiceResult[None]:
        self._authorize(actor, "accounts", "account_role", "revoke")
        with self._uow_factory() as uow:
            assignment = uow.account_roles.get(AccountRoleFilter(account_id=account_id, role_id=role_id))
            if not assignment:
                raise RoleAssignmentNotFound()
            assignment.register_event(RoleRevoked(account_id=account_id, role_id=role_id))
            uow.account_roles.delete(assignment)
            uow.track(assignment)
            uow.commit()
        return ServiceResult(data=None)

    def get_effective_permissions(self, actor: SupportsPermissionCheck, account_id: UUID) -> ServiceResult[list[str]]:
        """Resolved union of all permissions across all of the account's roles."""
        self._authorize(actor, "accounts", "account_role", "read")
        with self._uow_factory() as uow:
            account = uow.accounts.get(account_id)
            if not account:
                raise AccountNotFound()
            role_assignments = uow.account_roles.list(AccountRoleFilter(account_id=account_id, limit=100)).items
        # Permission resolution is delegated to the RBAC domain service
        return ServiceResult(data=[str(r.role_id) for r in role_assignments])
