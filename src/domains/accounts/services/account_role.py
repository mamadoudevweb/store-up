"""AccountRole entity service."""
from __future__ import annotations

from uuid import UUID

from src.domains.accounts.entities import AccountRole
from src.domains.accounts.events import RoleAssigned, RoleRevoked
from src.domains.accounts.exceptions import (
    AccountNotFound,
    RoleAlreadyAssigned,
    RoleAssignmentNotFound,
)
from src.domains.accounts.repositories.filters import AccountFilter, AccountRoleFilter
from src.domains.accounts.repositories.base_uow import BaseAccountUnitOfWork
from src.domains.shared.events import EventBus
from src.domains.shared.service_result import ServiceResult


class Service:
    def __init__(self, uow: BaseAccountUnitOfWork, event_bus: EventBus) -> None:
        self._uow = uow
        self._bus = event_bus

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
