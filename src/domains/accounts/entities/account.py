"""Account entity."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from src.core.entities.base_entity import Entity

class AccountStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"

@dataclass(kw_only=True)
class Account(Entity):
    """Identity entity — no login info, no roles."""
    id: UUID
    first_name: str
    last_name: str
    birth_date: date | None
    status: AccountStatus
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(
        cls,
        first_name: str,
        last_name: str,
        birth_date: date | None = None,
    ) -> "Account":
        account = cls(
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date,
            status=AccountStatus.ACTIVE,
        )
        from src.domains.accounts.events import AccountCreated
        account.register_event(AccountCreated(account_id=account.id))
        return account

    def suspend(self) -> None:
        self.status = AccountStatus.SUSPENDED
        self.updated_at = datetime.now(timezone.utc)
        from src.domains.accounts.events import AccountSuspended
        self.register_event(AccountSuspended(account_id=self.id))

    def update(
        self,
        first_name: str | None = None,
        last_name: str | None = None,
        birth_date: date | None = None,
    ) -> None:
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if birth_date is not None:
            self.birth_date = birth_date
        self.updated_at = datetime.now(timezone.utc)
        from src.domains.accounts.events import AccountUpdated
        self.register_event(AccountUpdated(account_id=self.id))

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def is_active(self) -> bool:
        return self.status == AccountStatus.ACTIVE

