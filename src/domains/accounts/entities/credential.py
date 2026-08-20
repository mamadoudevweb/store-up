"""Credential entity."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.core.entities.base_entity import Entity

@dataclass(kw_only=True)
class Credential(Entity):
    """Login credential entity — separated from Account identity."""
    id: UUID
    account_id: UUID
    username: str
    email: str
    password_hash: str
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

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
        cred.register_event(CredentialSet(account_id=account_id, credential_id=cred.id))
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
        self.register_event(CredentialUpdated(account_id=self.account_id))

    def record_login(self) -> None:
        self.last_login_at = datetime.now(timezone.utc)
