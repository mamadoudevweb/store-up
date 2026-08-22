"""AccountRole ORM model."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domains.accounts.repositories.sql.orms.account_model import AccountModel
from sqlalchemy import DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.extensions import db


class AccountRoleModel(db.Model):  # type: ignore[name-defined]
    __tablename__ = "account_roles"

    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    domain_scope: Mapped[str | None] = mapped_column(String(100), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    account: Mapped["AccountModel"] = relationship("AccountModel", back_populates="roles")
