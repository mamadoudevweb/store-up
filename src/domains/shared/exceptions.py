"""
Base exception hierarchy.

Every domain defines its own exceptions in their own scope (domain/exceptions.py),
all extending AppError from here. The app-level error handler catches AppError
and converts it to the envelope JSON response.
"""
from __future__ import annotations

from http import HTTPStatus


class AppError(Exception):
    """Base application exception.

    Subclasses set class-level ``code`` and ``http_status``.
    They may also override ``message`` or accept it as a constructor arg.
    """

    code: str = "APPLICATION_ERROR"
    http_status: int = HTTPStatus.INTERNAL_SERVER_ERROR
    message: str = "An application error occurred"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.message
        super().__init__(self.message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"


# ── Generic fallback errors (app-level, not domain-level) ──────────────────────

class NotFoundError(AppError):
    code = "NOT_FOUND"
    http_status = HTTPStatus.NOT_FOUND
    message = "Resource not found"


class ConflictError(AppError):
    code = "CONFLICT"
    http_status = HTTPStatus.CONFLICT
    message = "Resource already exists"


class ValidationError(AppError):
    code = "VALIDATION_ERROR"
    http_status = HTTPStatus.UNPROCESSABLE_ENTITY
    message = "Validation failed"


class PermissionDeniedError(AppError):
    code = "PERMISSION_DENIED"
    http_status = HTTPStatus.FORBIDDEN
    message = "You do not have permission to perform this action"


class UnauthorizedError(AppError):
    code = "UNAUTHORIZED"
    http_status = HTTPStatus.UNAUTHORIZED
    message = "Authentication required"
