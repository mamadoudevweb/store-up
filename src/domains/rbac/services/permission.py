"""Permission service."""
from __future__ import annotations

import uuid
from typing import Sequence

from src.domains.rbac.entities import Permission
from src.domains.rbac.events import PermissionCreated
from src.domains.rbac.exceptions import PermissionAlreadyExists, PermissionNotFound
from src.domains.rbac.repositories.base_uow import RbacUnitOfWork
from src.domains.rbac.repositories.filters import PermissionFilter
from src.domains.shared.events import EventBus
from src.domains.shared.pagination import Paginated
from src.domains.shared.service_result import ServiceResult


class PermissionService:
    def __init__(self, uow: RbacUnitOfWork, bus: EventBus) -> None:
        self._uow = uow
        self._bus = bus

    def create_permission(self, resource: str, action: str, description: str | None = None) -> ServiceResult[Permission]:
        with self._uow as uow:
            if uow.permissions.exists(PermissionFilter(resource=resource, action=action)):
                raise PermissionAlreadyExists(f"Permission '{resource}:{action}' already exists.")

            permission = Permission(resource=resource, action=action, description=description)
            uow.permissions.add(permission)
            uow.commit()

            self._bus.publish(PermissionCreated(
                permission_id=permission.id,
                resource=permission.resource,
                action=permission.action,
            ))
            return ServiceResult.ok(permission)

    def get_permission(self, permission_id: str | uuid.UUID) -> ServiceResult[Permission]:
        if isinstance(permission_id, str):
            permission_id = uuid.UUID(permission_id)

        with self._uow as uow:
            permission = uow.permissions.get(PermissionFilter(id=permission_id))
            if not permission:
                raise PermissionNotFound(f"Permission '{permission_id}' not found.")
            return ServiceResult.ok(permission)

    def list_role_permissions(self, role_id: str | uuid.UUID) -> ServiceResult[Paginated[Permission]]:
        if isinstance(role_id, str):
            role_id = uuid.UUID(role_id)

        with self._uow as uow:
            paginated = uow.permissions.list(PermissionFilter(role_id=role_id))
            return ServiceResult.ok(paginated)

    def check_roles_have_permission(self, role_ids: list[str | uuid.UUID], resource: str, action: str) -> ServiceResult[bool]:
        """Return True if ANY of the given roles has the requested permission."""
        parsed_ids = [uuid.UUID(r) if isinstance(r, str) else r for r in role_ids]

        with self._uow as uow:
            permission = uow.permissions.get(PermissionFilter(resource=resource, action=action))
            if not permission:
                return ServiceResult.ok(False)

            for role_id in parsed_ids:
                paginated = uow.permissions.list(PermissionFilter(role_id=role_id))
                if any(p.id == permission.id for p in paginated.items):
                    return ServiceResult.ok(True)

            return ServiceResult.ok(False)
