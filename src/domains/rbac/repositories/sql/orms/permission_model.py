"""Permission ORM model."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.domains.rbac.repositories.sql.orms.role_model import RoleModel

from sqlalchemy import DateTime, String, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.extensions import db


class PermissionModel(db.Model):  # type: ignore[name-defined]
    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resource: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("resource", "action", name="uq_permission_resource_action"),
    )

    roles: Mapped[List["RoleModel"]] = relationship(
        "RoleModel",
        secondary="role_permissions",
        back_populates="permissions"
    )
