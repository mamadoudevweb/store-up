"""Account ORM model."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.extensions import db


class AccountModel(db.Model):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    credential: Mapped["CredentialModel | None"] = relationship(
        "CredentialModel", back_populates="account", uselist=False, cascade="all, delete-orphan"
    )
    roles: Mapped[list["AccountRoleModel"]] = relationship(
        "AccountRoleModel", back_populates="account", cascade="all, delete-orphan"
    )
