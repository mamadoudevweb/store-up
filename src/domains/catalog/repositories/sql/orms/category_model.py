"""Category SQLAlchemy model."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.app.extensions import db


class CategoryModel(db.Model):  # type: ignore[name-defined]
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
