"""RolePermission service — manages role↔permission assignments."""
from __future__ import annotations

import uuid
from typing import Callable

from src.core.services.base_service import BaseService
from src.core.services.result import ServiceResult
from src.core.repositories.base_uow import BaseUnitOfWork
from src.domains.rbac.entities import RolePermission
from src.domains.rbac.events import RolePermissionAssigned, RolePermissionRevoked
from src.domains.rbac.exceptions import PermissionNotFound, RoleNotFound
from src.domains.rbac.repositories.filters import RolePermissionFilter


class RolePermissionService(BaseService):
    def __init__(self, uow_factory: Callable[[], BaseUnitOfWork]) -> None:
        super().__init__(uow_factory)

    def assign(self, role_id: str | uuid.UUID, permission_id: str | uuid.UUID) -> ServiceResult[RolePermission]:
        if isinstance(role_id, str):
            role_id = uuid.UUID(role_id)
        if isinstance(permission_id, str):
            permission_id = uuid.UUID(permission_id)

        with self._uow_factory() as uow:
            if not uow.roles.exists(id=role_id):
                raise RoleNotFound()
            if not uow.permissions.exists(id=permission_id):
                raise PermissionNotFound()
            
            # Idempotent — skip if already assigned
            if not uow.role_permissions.exists(role_id=role_id, permission_id=permission_id):
                rp = RolePermission(role_id=role_id, permission_id=permission_id)
                uow.role_permissions.add(rp)
                uow.commit()
                return ServiceResult(data=rp)

            # Already assigned — return existing
            existing = uow.role_permissions.get(RolePermissionFilter(role_id=role_id, permission_id=permission_id))
            return ServiceResult(data=existing)

    def revoke(self, role_id: str | uuid.UUID, permission_id: str | uuid.UUID) -> ServiceResult[None]:
        if isinstance(role_id, str):
            role_id = uuid.UUID(role_id)
        if isinstance(permission_id, str):
            permission_id = uuid.UUID(permission_id)

        with self._uow_factory() as uow:
            if not uow.roles.exists(id=role_id):
                raise RoleNotFound()

            rp = uow.role_permissions.get(RolePermissionFilter(role_id=role_id, permission_id=permission_id))
            if rp:
                uow.role_permissions.delete(rp)
                uow.commit()

            return ServiceResult(data=None)

    def list_for_role(self, role_id: str | uuid.UUID) -> ServiceResult[list[RolePermission]]:
        if isinstance(role_id, str):
            role_id = uuid.UUID(role_id)

        with self._uow_factory() as uow:
            paginated = uow.role_permissions.list(RolePermissionFilter(role_id=role_id))
            return ServiceResult(data=paginated.items)
