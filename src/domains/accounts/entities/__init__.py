"""Accounts domain — Account, Credential, AccountRole entities."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class AccountStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


@dataclass
class Account:
    """Identity entity — no login info, no roles."""

    id: UUID
    first_name: str
    last_name: str
    birth_date: date | None
    status: AccountStatus
    created_at: datetime
    updated_at: datetime

    # Collected domain events (populated by business methods)
    _events: list = field(default_factory=list, repr=False, compare=False)

    @classmethod
    def create(
        cls,
        first_name: str,
        last_name: str,
        birth_date: date | None = None,
    ) -> "Account":
        now = datetime.now(timezone.utc)
        account = cls(
            id=uuid4(),
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date,
            status=AccountStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        from src.domains.accounts.events import AccountCreated
        account._events.append(AccountCreated(account_id=account.id))
        return account

    def suspend(self) -> None:
        self.status = AccountStatus.SUSPENDED
        self.updated_at = datetime.now(timezone.utc)
        from src.domains.accounts.events import AccountSuspended
        self._events.append(AccountSuspended(account_id=self.id))

    def update(self, first_name: str | None = None, last_name: str | None = None,
               birth_date: date | None = None) -> None:
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if birth_date is not None:
            self.birth_date = birth_date
        self.updated_at = datetime.now(timezone.utc)
        from src.domains.accounts.events import AccountUpdated
        self._events.append(AccountUpdated(account_id=self.id))

    def pull_events(self) -> list:
        events = list(self._events)
        self._events.clear()
        return events

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def is_active(self) -> bool:
        return self.status == AccountStatus.ACTIVE


@dataclass
class Credential:
    """Login credential entity — separated from Account identity."""

    id: UUID
    account_id: UUID
    username: str
    email: str
    password_hash: str
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

    _events: list = field(default_factory=list, repr=False, compare=False)

    @classmethod
    def create(
        cls,
        account_id: UUID,
        username: str,
        email: str,
        password_hash: str,
    ) -> "Credential":
        now = datetime.now(timezone.utc)
        cred = cls(
            id=uuid4(),
            account_id=account_id,
            username=username,
            email=email,
            password_hash=password_hash,
            last_login_at=None,
            created_at=now,
            updated_at=now,
        )
        from src.domains.accounts.events import CredentialSet
        cred._events.append(CredentialSet(account_id=account_id, credential_id=cred.id))
        return cred

    def update(
        self,
        username: str | None = None,
        email: str | None = None,
        password_hash: str | None = None,
    ) -> None:
        if username is not None:
            self.username = username
        if email is not None:
            self.email = email
        if password_hash is not None:
            self.password_hash = password_hash
        self.updated_at = datetime.now(timezone.utc)
        from src.domains.accounts.events import CredentialUpdated
        self._events.append(CredentialUpdated(account_id=self.account_id))

    def record_login(self) -> None:
        self.last_login_at = datetime.now(timezone.utc)

    def pull_events(self) -> list:
        events = list(self._events)
        self._events.clear()
        return events


@dataclass
class AccountRole:
    """Association between an Account and a Role, optionally scoped to a domain."""

    account_id: UUID
    role_id: UUID
    domain_scope: str | None  # e.g. "inventory" — None means global
    assigned_at: datetime
    assigned_by: UUID | None

    @classmethod
    def create(
        cls,
        account_id: UUID,
        role_id: UUID,
        assigned_by: UUID | None = None,
        domain_scope: str | None = None,
    ) -> "AccountRole":
        return cls(
            account_id=account_id,
            role_id=role_id,
            domain_scope=domain_scope,
            assigned_at=datetime.now(timezone.utc),
            assigned_by=assigned_by,
        )
