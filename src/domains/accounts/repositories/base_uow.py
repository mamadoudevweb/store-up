"""Base UoW for accounts domain."""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.domains.accounts.entities import Account, AccountRole, Credential
from src.domains.accounts.repositories.filters import (
    AccountFilter,
    AccountRoleFilter,
    CredentialFilter,
)
from src.domains.shared.repositories import BaseRepository


class BaseAccountUnitOfWork(ABC):
    """Owns the session lifecycle. Services use UoW, never raw sessions."""

    accounts: BaseRepository[Account, AccountFilter]
    credentials: BaseRepository[Credential, CredentialFilter]
    account_roles: BaseRepository[AccountRole, AccountRoleFilter]

    @abstractmethod
    def __enter__(self) -> "BaseAccountUnitOfWork":
        ...

    @abstractmethod
    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        ...

    @abstractmethod
    def commit(self) -> None:
        ...

    @abstractmethod
    def rollback(self) -> None:
        ...
