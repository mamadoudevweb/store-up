"""RBAC service layer."""
from __future__ import annotations
from typing import Callable

from src.core.services.base_service import BaseService
from src.core.repositories.base_uow import BaseUnitOfWork

from .role import RoleService
from .permission import PermissionService
from .role_permission import RolePermissionService


class RbacDomainService(BaseService):
    """Facade for RBAC domain services."""

    def __init__(self, uow_factory: Callable[[], BaseUnitOfWork]) -> None:
        super().__init__(uow_factory)
        
        self.role = RoleService(uow_factory)
        self.permission = PermissionService(uow_factory)
        self.role_permission = RolePermissionService(uow_factory)
