"""Base Unit of Work for RBAC domain."""
from __future__ import annotations

import abc

from src.domains.rbac.entities import Permission, Role
from src.domains.rbac.repositories.filters import PermissionFilter, RoleFilter
from src.domains.shared.repositories import BaseRepository


class RbacUnitOfWork(abc.ABC):
    roles: BaseRepository[Role, RoleFilter]
    permissions: BaseRepository[Permission, PermissionFilter]

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

    @abc.abstractmethod
    def add_permission_to_role(self, role_id: str, permission_id: str) -> None:
        pass

    @abc.abstractmethod
    def remove_permission_from_role(self, role_id: str, permission_id: str) -> None:
        pass
