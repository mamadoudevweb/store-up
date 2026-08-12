"""RBAC Domain Entities."""
from .permission import Permission
from .role import Role
from .role_permission import RolePermission

__all__ = ["Role", "Permission", "RolePermission"]
