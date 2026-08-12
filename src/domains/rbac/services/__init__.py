"""RBAC service layer."""
from __future__ import annotations

from src.domains.rbac.repositories.base_uow import RbacUnitOfWork
from src.domains.shared.events import EventBus

from .role import RoleService
from .permission import PermissionService
from .role_permission import RolePermissionService


class RbacService:
    """Facade for RBAC domain services."""

    def __init__(self, uow: RbacUnitOfWork, bus: EventBus) -> None:
        self._uow = uow
        self._bus = bus
        
        self.role = RoleService(uow, bus)
        self.permission = PermissionService(uow, bus)
        self.role_permission = RolePermissionService(uow, bus)
