from typing import Any

class AppError(Exception):
    """Base of every error in the system. Subclassing (anywhere, including
    inside a domain package) auto-registers the error by its `code` — no
    manual registry to maintain."""
    code: str = "APP_ERROR"
    status_code: int = 400
    message: str = "An error occurred"

    _registry: dict[str, type["AppError"]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        AppError._registry[cls.code] = cls

    def __init__(self, message: str | None = None, **details: Any) -> None:
        self.message: str = message or self.message
        self.details: dict[str, Any] = details
        super().__init__(self.message)

# Generic, cross-domain errors. Domains raise these directly when nothing
# more specific applies, or subclass them for a business-specific case.
class NotFoundError(AppError):
    code, status_code, message = "NOT_FOUND", 404, "Resource not found"

class ValidationError(AppError):
    code, status_code, message = "VALIDATION_ERROR", 422, "Invalid data"

class PermissionDeniedError(AppError):
    code, status_code, message = "PERMISSION_DENIED", 403, "Permission denied"

class ConflictError(AppError):
    code, status_code, message = "CONFLICT", 409, "Conflicting state"

ERROR_REGISTRY: dict[str, type[AppError]] = AppError._registry
