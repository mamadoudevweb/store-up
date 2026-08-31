"""RolePermission service — manages role↔permission assignments."""
from __future__ import annotations

import uuid
from typing import Callable

from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.result import ServiceResult
from src.core.repositories.base_uow import BaseUnitOfWork
from src.domains.rbac.entities import RolePermission
from src.domains.rbac.events import RolePermissionAssigned, RolePermissionRevoked
from src.domains.rbac.exceptions import PermissionNotFound, RoleNotFound
from src.domains.rbac.repositories.filters import RolePermissionFilter, RoleFilter, PermissionFilter


class RolePermissionService(BaseService):
    def __init__(self, uow_factory: Callable[[], BaseUnitOfWork]) -> None:
        super().__init__(uow_factory)

    def assign(self, actor: SupportsPermissionCheck, role_id: str | uuid.UUID, permission_id: str | uuid.UUID) -> ServiceResult[RolePermission]:
        self._authorize(actor, "rbac", "role_permission", "assign")
        if isinstance(role_id, str):
            role_id = uuid.UUID(role_id)
        if isinstance(permission_id, str):
            permission_id = uuid.UUID(permission_id)

        with self._uow_factory() as uow:
            if not uow.roles.exists(RoleFilter(id=role_id)):
                raise RoleNotFound()
            if not uow.permissions.exists(PermissionFilter(id=permission_id)):
                raise PermissionNotFound()
            
            # Idempotent — skip if already assigned
            if uow.role_permissions.exists(RolePermissionFilter(role_id=role_id, permission_id=permission_id)):
                existing = uow.role_permissions.get(RolePermissionFilter(role_id=role_id, permission_id=permission_id))
                return ServiceResult(data=existing)

            # Check if it was previously revoked
            if uow.role_permissions.exists(RolePermissionFilter(role_id=role_id, permission_id=permission_id, active_only=False)):
                rp = uow.role_permissions.get(RolePermissionFilter(role_id=role_id, permission_id=permission_id, active_only=False))
                if rp:
                    rp.reactivate()
                    uow.role_permissions.update(rp)
                    uow.track(rp)
                    return ServiceResult(data=rp)

            # New assignment
            rp = RolePermission.assign_permission(role_id=role_id, permission_id=permission_id)
            uow.role_permissions.add(rp)
            uow.track(rp)
            return ServiceResult(data=rp)

    def revoke(self, actor: SupportsPermissionCheck, role_id: str | uuid.UUID, permission_id: str | uuid.UUID) -> ServiceResult[None]:
        self._authorize(actor, "rbac", "role_permission", "revoke")
        if isinstance(role_id, str):
            role_id = uuid.UUID(role_id)
        if isinstance(permission_id, str):
            permission_id = uuid.UUID(permission_id)

        with self._uow_factory() as uow:
            if not uow.roles.exists(RoleFilter(id=role_id)):
                raise RoleNotFound()

            rp = uow.role_permissions.get(RolePermissionFilter(role_id=role_id, permission_id=permission_id))
            if rp:
                rp.revoke_permission()
                uow.role_permissions.update(rp)
                uow.track(rp)

            return ServiceResult(data=None)

    def list_for_role(self, actor: SupportsPermissionCheck, role_id: str | uuid.UUID) -> ServiceResult[list[RolePermission]]:
        self._authorize(actor, "rbac", "role_permission", "list")
        if isinstance(role_id, str):
            role_id = uuid.UUID(role_id)

        with self._uow_factory() as uow:
            paginated = uow.role_permissions.list(RolePermissionFilter(role_id=role_id))
            return ServiceResult(data=paginated.items)
