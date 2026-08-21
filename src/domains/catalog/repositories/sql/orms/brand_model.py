"""Brand SQLAlchemy model."""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.app.extensions import db


class BrandModel(db.Model):  # type: ignore[name-defined]
    __tablename__ = "brands"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
