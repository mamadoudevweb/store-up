"""Auth domain exceptions."""
from __future__ import annotations

from src.domains.shared.exceptions import DomainException


class InvalidCredentials(DomainException):
    def __init__(self, message: str = "Invalid username or password") -> None:
        super().__init__(message)


class TokenRevoked(DomainException):
    def __init__(self, message: str = "Token has been revoked") -> None:
        super().__init__(message)


class TokenDecodeError(DomainException):
    def __init__(self, message: str = "Failed to decode token") -> None:
        super().__init__(message)
