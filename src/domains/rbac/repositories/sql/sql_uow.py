"""SQL Unit of Work for RBAC domain."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy.orm import Session

from src.domains.rbac.repositories.base_uow import RbacUnitOfWork
from src.domains.rbac.repositories.sql.orms import RoleModel, PermissionModel, RolePermissionModel
from src.domains.rbac.repositories.sql.permission_repository import SqlPermissionRepository
from src.domains.rbac.repositories.sql.role_repository import SqlRoleRepository


class SqlRbacUnitOfWork(RbacUnitOfWork):
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self.session_factory = session_factory
        self.session: Session | None = None

    def __enter__(self) -> SqlRbacUnitOfWork:
        self.session = self.session_factory()
        self.roles = SqlRoleRepository(self.session)
        self.permissions = SqlPermissionRepository(self.session)
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

    def add_permission_to_role(self, role_id: str | uuid.UUID, permission_id: str | uuid.UUID) -> None:
        if isinstance(role_id, str):
            role_id = uuid.UUID(role_id)
        if isinstance(permission_id, str):
            permission_id = uuid.UUID(permission_id)

        role = self.session.get(RoleModel, role_id)
        permission = self.session.get(PermissionModel, permission_id)

        if role and permission:
            # Check if it already exists
            exists = any(p.id == permission_id for p in role.permissions)
            if not exists:
                role.permissions.append(permission)
                self.session.flush()

    def remove_permission_from_role(self, role_id: str | uuid.UUID, permission_id: str | uuid.UUID) -> None:
        if isinstance(role_id, str):
            role_id = uuid.UUID(role_id)
        if isinstance(permission_id, str):
            permission_id = uuid.UUID(permission_id)

        role = self.session.get(RoleModel, role_id)
        permission = self.session.get(PermissionModel, permission_id)

        if role and permission:
            # Check if it already exists
            if permission in role.permissions:
                role.permissions.remove(permission)
                self.session.flush()
