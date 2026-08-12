"""RolePermission service — manages role↔permission assignments."""
from __future__ import annotations

import uuid

from src.domains.rbac.entities import RolePermission
from src.domains.rbac.events import RolePermissionAssigned, RolePermissionRevoked
from src.domains.rbac.exceptions import PermissionNotFound, RoleNotFound
from src.domains.rbac.repositories.base_uow import RbacUnitOfWork
from src.domains.rbac.repositories.filters import PermissionFilter, RoleFilter, RolePermissionFilter
from src.domains.shared.events import EventBus
from src.domains.shared.service_result import ServiceResult


class RolePermissionService:
    def __init__(self, uow: RbacUnitOfWork, bus: EventBus) -> None:
        self._uow = uow
        self._bus = bus

    def assign(self, role_id: str | uuid.UUID, permission_id: str | uuid.UUID) -> ServiceResult[RolePermission]:
        if isinstance(role_id, str):
            role_id = uuid.UUID(role_id)
        if isinstance(permission_id, str):
            permission_id = uuid.UUID(permission_id)

        with self._uow as uow:
            if not uow.roles.exists(RoleFilter(id=role_id)):
                raise RoleNotFound()
            if not uow.permissions.exists(PermissionFilter(id=permission_id)):
                raise PermissionNotFound()
            
            # Idempotent — skip if already assigned
            if not uow.role_permissions.exists(RolePermissionFilter(role_id=role_id, permission_id=permission_id)):
                rp = RolePermission(role_id=role_id, permission_id=permission_id)
                uow.role_permissions.add(rp)
                uow.commit()
                self._bus.publish(RolePermissionAssigned(role_id=role_id, permission_id=permission_id))
                return ServiceResult.ok(rp)

            # Already assigned — return existing
            existing = uow.role_permissions.get(RolePermissionFilter(role_id=role_id, permission_id=permission_id))
            return ServiceResult.ok(existing)

    def revoke(self, role_id: str | uuid.UUID, permission_id: str | uuid.UUID) -> ServiceResult[None]:
        if isinstance(role_id, str):
            role_id = uuid.UUID(role_id)
        if isinstance(permission_id, str):
            permission_id = uuid.UUID(permission_id)

        with self._uow as uow:
            if not uow.roles.exists(RoleFilter(id=role_id)):
                raise RoleNotFound()

            rp = uow.role_permissions.get(RolePermissionFilter(role_id=role_id, permission_id=permission_id))
            if rp:
                uow.role_permissions.delete(rp)
                uow.commit()
                self._bus.publish(RolePermissionRevoked(role_id=role_id, permission_id=permission_id))

            return ServiceResult.ok(None)

    def list_for_role(self, role_id: str | uuid.UUID) -> ServiceResult[list[RolePermission]]:
        if isinstance(role_id, str):
            role_id = uuid.UUID(role_id)

        with self._uow as uow:
            paginated = uow.role_permissions.list(RolePermissionFilter(role_id=role_id))
            return ServiceResult.ok(paginated.items)
