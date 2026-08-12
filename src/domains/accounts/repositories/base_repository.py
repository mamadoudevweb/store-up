"""Abstract base repositories for the accounts domain."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.domains.accounts.entities import Account, AccountRole, Credential
from src.domains.shared.filters import BaseFilter
from src.domains.shared.pagination import Paginated


class AccountFilter(BaseFilter):
    search: str | None = None
    status: str | None = None


class BaseAccountRepository(ABC):

    @abstractmethod
    def add(self, entity: Account) -> Account: ...

    @abstractmethod
    def get(self, entity_id: UUID) -> Account | None: ...

    @abstractmethod
    def list(self, filters: AccountFilter) -> Paginated[Account]: ...

    @abstractmethod
    def _apply_filter(self, query: object, filters: AccountFilter) -> object: ...

    @abstractmethod
    def update(self, entity: Account) -> Account: ...

    @abstractmethod
    def delete(self, entity: Account) -> None: ...


class BaseCredentialRepository(ABC):

    @abstractmethod
    def add(self, entity: Credential) -> Credential: ...

    @abstractmethod
    def get(self, entity_id: UUID) -> Credential | None: ...

    @abstractmethod
    def get_by_account(self, account_id: UUID) -> Credential | None: ...

    @abstractmethod
    def get_by_username(self, username: str) -> Credential | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> Credential | None: ...

    @abstractmethod
    def get_by_username_or_email(self, value: str) -> Credential | None: ...

    @abstractmethod
    def list(self, filters: BaseFilter) -> Paginated[Credential]: ...

    @abstractmethod
    def _apply_filter(self, query: object, filters: BaseFilter) -> object: ...

    @abstractmethod
    def update(self, entity: Credential) -> Credential: ...

    @abstractmethod
    def delete(self, entity: Credential) -> None: ...


class BaseAccountRoleRepository(ABC):

    @abstractmethod
    def add(self, entity: AccountRole) -> AccountRole: ...

    @abstractmethod
    def get(self, account_id: UUID, role_id: UUID) -> AccountRole | None: ...

    @abstractmethod
    def list_by_account(self, account_id: UUID) -> list[AccountRole]: ...

    @abstractmethod
    def list(self, filters: BaseFilter) -> Paginated[AccountRole]: ...

    @abstractmethod
    def _apply_filter(self, query: object, filters: BaseFilter) -> object: ...

    @abstractmethod
    def update(self, entity: AccountRole) -> AccountRole: ...

    @abstractmethod
    def delete(self, entity: AccountRole) -> None: ...
