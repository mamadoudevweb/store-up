"""RBAC domain exceptions."""
from __future__ import annotations

from src.core.services.errors import AppError


class RoleNotFound(AppError):
    code = "ROLE_NOT_FOUND"
    http_status = 404

    def __init__(self, message: str = "Role not found.") -> None:
        super().__init__(message=message)


class RoleAlreadyExists(AppError):
    code = "ROLE_ALREADY_EXISTS"
    http_status = 409

    def __init__(self, message: str = "Role already exists.") -> None:
        super().__init__(message=message)


class PermissionNotFound(AppError):
    code = "PERMISSION_NOT_FOUND"
    http_status = 404

    def __init__(self, message: str = "Permission not found.") -> None:
        super().__init__(message=message)


class PermissionAlreadyExists(AppError):
    code = "PERMISSION_ALREADY_EXISTS"
    http_status = 409

    def __init__(self, message: str = "Permission already exists.") -> None:
        super().__init__(message=message)
