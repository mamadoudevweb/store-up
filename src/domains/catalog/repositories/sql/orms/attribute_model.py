"""Attribute and AttributeValue SQLAlchemy models."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.app.extensions import db


class AttributeModel(db.Model):  # type: ignore[name-defined]
    __tablename__ = "attributes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), server_default=func.now()
    )


class AttributeValueModel(db.Model):  # type: ignore[name-defined]
    __tablename__ = "attribute_values"
    __table_args__ = (UniqueConstraint("attribute_id", "value", name="uq_attribute_value"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    attribute_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("attributes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    value: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), server_default=func.now()
    )
