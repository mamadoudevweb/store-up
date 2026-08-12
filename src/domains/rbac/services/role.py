"""Role service."""
from __future__ import annotations

import uuid

from src.domains.rbac.entities import Role
from src.domains.rbac.events import RoleCreated, RolePermissionAssigned, RolePermissionRevoked
from src.domains.rbac.exceptions import PermissionNotFound, RoleAlreadyExists, RoleNotFound
from src.domains.rbac.repositories.base_uow import RbacUnitOfWork
from src.domains.rbac.repositories.filters import PermissionFilter, RoleFilter
from src.domains.shared.events import EventBus
from src.domains.shared.service_result import ServiceResult


class RoleService:
    def __init__(self, uow: RbacUnitOfWork, bus: EventBus) -> None:
        self._uow = uow
        self._bus = bus

    def create_role(self, name: str, description: str | None = None) -> ServiceResult[Role]:
        with self._uow as uow:
            if uow.roles.exists(RoleFilter(name=name)):
                raise RoleAlreadyExists(f"Role '{name}' already exists.")

            role = Role(name=name, description=description)
            uow.roles.add(role)
            uow.commit()

            self._bus.publish(RoleCreated(role_id=role.id, name=role.name))
            return ServiceResult.ok(role)

    def get_role(self, role_id: str | uuid.UUID) -> ServiceResult[Role]:
        if isinstance(role_id, str):
            role_id = uuid.UUID(role_id)

        with self._uow as uow:
            role = uow.roles.get(RoleFilter(id=role_id))
            if not role:
                raise RoleNotFound(f"Role '{role_id}' not found.")
            return ServiceResult.ok(role)
