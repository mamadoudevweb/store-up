"""Inventory SQLAlchemy models."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Integer, String, DateTime, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.app.extensions import db


class InventoryItemModel(db.Model):  # type: ignore[name-defined]
    __tablename__ = "inventory_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(unique=True, nullable=False, index=True)
    quantity_on_hand: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity_reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        CheckConstraint("quantity_on_hand >= 0", name="chk_quantity_on_hand_positive"),
        CheckConstraint("quantity_reserved >= 0", name="chk_quantity_reserved_positive"),
        CheckConstraint("quantity_on_hand >= quantity_reserved", name="chk_reserved_not_exceed_on_hand"),
    )


class StockMovementModel(db.Model):  # type: ignore[name-defined]
    __tablename__ = "stock_movements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    quantity_change: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        server_default=func.now()
    )
