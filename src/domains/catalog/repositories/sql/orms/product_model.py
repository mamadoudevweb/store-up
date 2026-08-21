"""Product SQLAlchemy model."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.app.extensions import db


class ProductModel(db.Model):  # type: ignore[name-defined]
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    cost_price: Mapped[int] = mapped_column(Integer, nullable=False)  # stored in cents
    sell_price: Mapped[int] = mapped_column(Integer, nullable=False)  # stored in cents
    
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("brands.id", ondelete="SET NULL"), nullable=True
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
