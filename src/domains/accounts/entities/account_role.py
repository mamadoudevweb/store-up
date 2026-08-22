"""AccountRole entity."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from src.core.entities.base_entity import Entity

@dataclass(kw_only=True)
class AccountRole(Entity[UUID]):
    """Association between an Account and a Role, optionally scoped to a domain."""
    account_id: UUID
    role_id: UUID
    domain_scope: str | None
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
