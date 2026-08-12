"""Base Unit of Work for RBAC domain."""
from __future__ import annotations

import abc

from src.domains.rbac.entities import Permission, Role, RolePermission
from src.domains.rbac.repositories.filters import PermissionFilter, RoleFilter, RolePermissionFilter
from src.domains.shared.repositories import BaseRepository


class RbacUnitOfWork(abc.ABC):
    roles: BaseRepository[Role, RoleFilter]
    permissions: BaseRepository[Permission, PermissionFilter]
    role_permissions: BaseRepository[RolePermission, RolePermissionFilter]

    def __enter__(self) -> RbacUnitOfWork:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.rollback()

    @abc.abstractmethod
    def commit(self) -> None:
        pass

    @abc.abstractmethod
    def rollback(self) -> None:
        pass
