"""Role ORM model."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from sqlalchemy import DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.extensions import db


class RoleModel(db.Model):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    permissions: Mapped[List["PermissionModel"]] = relationship(
        "PermissionModel",
        secondary="role_permissions",
        back_populates="roles"
    )
