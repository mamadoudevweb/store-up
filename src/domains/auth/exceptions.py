"""Auth domain exceptions."""
from __future__ import annotations

from src.core.services.errors import AppError


class InvalidCredentials(AppError):
    code = "INVALID_CREDENTIALS"
    status_code = 401
    
    def __init__(self, message: str = "Invalid username or password.") -> None:
        super().__init__(message=message)


class TokenRevoked(AppError):
    code = "TOKEN_REVOKED"
    status_code = 401
    
    def __init__(self, message: str = "Token has been revoked") -> None:
        super().__init__(message=message)


class TokenDecodeError(AppError):
    code = "TOKEN_DECODE_ERROR"
    status_code = 401
    
    def __init__(self, message: str = "Failed to decode token") -> None:
        super().__init__(message=message)
