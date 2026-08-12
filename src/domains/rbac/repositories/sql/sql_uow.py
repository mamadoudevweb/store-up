"""SQL Unit of Work for RBAC domain."""
from __future__ import annotations

from typing import Callable

from sqlalchemy.orm import Session

from src.domains.rbac.repositories.base_uow import RbacUnitOfWork
from src.domains.rbac.repositories.sql.permission_repository import SqlPermissionRepository
from src.domains.rbac.repositories.sql.role_permission_repository import SqlRolePermissionRepository
from src.domains.rbac.repositories.sql.role_repository import SqlRoleRepository


class SqlRbacUnitOfWork(RbacUnitOfWork):
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self.session_factory = session_factory
        self.session: Session | None = None

    def __enter__(self) -> SqlRbacUnitOfWork:
        self.session = self.session_factory()
        self.roles = SqlRoleRepository(self.session)
        self.permissions = SqlPermissionRepository(self.session)
        self.role_permissions = SqlRolePermissionRepository(self.session)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        super().__exit__(exc_type, exc_val, exc_tb)
        if self.session:
            self.session.close()

    def commit(self) -> None:
        if self.session:
            self.session.commit()

    def rollback(self) -> None:
        if self.session:
            self.session.rollback()
