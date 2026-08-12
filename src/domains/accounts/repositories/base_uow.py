"""Abstract Unit of Work for the accounts domain."""
from __future__ import annotations

from abc import ABC, abstractmethod

from .base_repository import (
    BaseAccountRepository,
    BaseAccountRoleRepository,
    BaseCredentialRepository,
)


class BaseAccountUnitOfWork(ABC):
    """Owns the session lifecycle. Services use UoW, never raw sessions."""

    accounts: BaseAccountRepository
    credentials: BaseCredentialRepository
    account_roles: BaseAccountRoleRepository

    @abstractmethod
    def __enter__(self) -> "BaseAccountUnitOfWork": ...

    @abstractmethod
    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None: ...

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...
