"""ServiceResult — the uniform return type for all service methods."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from .exceptions import AppError

T = TypeVar("T")


@dataclass
class ServiceResult(Generic[T]):
    """
    Uniform service return value.

    Services always return ServiceResult[T]. On success, data is populated.
    On failure, services raise AppError (subclasses) directly — the error
    handler in the app layer converts them to the HTTP envelope.

    ServiceResult is therefore always a success container; the error field
    is reserved for non-exceptional advisory information if needed.
    """

    success: bool
    data: T | None = None
    error: AppError | None = None

    @classmethod
    def ok(cls, data: T) -> "ServiceResult[T]":
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: AppError) -> "ServiceResult[T]":
        return cls(success=False, data=None, error=error)
