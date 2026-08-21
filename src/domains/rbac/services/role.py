"""Role service."""
from __future__ import annotations

import uuid
from typing import Callable

from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.result import ServiceResult
from src.core.repositories.base_uow import BaseUnitOfWork
from src.domains.rbac.entities import Role
from src.domains.rbac.events import RoleCreated
from src.domains.rbac.exceptions import RoleAlreadyExists, RoleNotFound
from src.domains.rbac.repositories.filters import RoleFilter


class RoleService(BaseService):
    def __init__(self, uow_factory: Callable[[], BaseUnitOfWork]) -> None:
        super().__init__(uow_factory)

    def create_role(self, actor: SupportsPermissionCheck, name: str, description: str | None = None) -> ServiceResult[Role]:
        self._authorize(actor, "rbac", "role", "create")
        with self._uow_factory() as uow:
            if uow.roles.exists(name=name):
                raise RoleAlreadyExists(f"Role '{name}' already exists.")

            role = Role(name=name, description=description)
            role = uow.roles.add(role)
            uow.commit()

            return ServiceResult(data=role)

    def get_role(self, actor: SupportsPermissionCheck, role_id: str | uuid.UUID) -> ServiceResult[Role]:
        self._authorize(actor, "rbac", "role", "read")
        if isinstance(role_id, str):
            role_id = uuid.UUID(role_id)

        with self._uow_factory() as uow:
            role = uow.roles.get(role_id)
            if not role:
                raise RoleNotFound(f"Role '{role_id}' not found.")
            return ServiceResult(data=role)

    def delete_role(self, actor: SupportsPermissionCheck, role_id: str | uuid.UUID) -> ServiceResult[None]:
        self._authorize(actor, "rbac", "role", "delete")
        if isinstance(role_id, str):
            role_id = uuid.UUID(role_id)
        
        with self._uow_factory() as uow:
            role = uow.roles.get(role_id)
            if not role:
                raise RoleNotFound(f"Role '{role_id}' not found.")
            uow.roles.delete(role)
            uow.commit()
            return ServiceResult(data=None)
