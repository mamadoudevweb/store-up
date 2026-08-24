"""Refund SQLAlchemy models."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Integer, String, DateTime, func, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.extensions import db


class RefundModel(db.Model):  # type: ignore[name-defined]
    __tablename__ = "refunds"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    sale_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sales.id"), nullable=False, index=True)
    processed_by: Mapped[uuid.UUID] = mapped_column(nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        server_default=func.now()
    )

    lines: Mapped[list[RefundLineModel]] = relationship(
        "RefundLineModel", back_populates="refund", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processed', 'failed')", 
            name="chk_refund_status"
        ),
    )


class RefundLineModel(db.Model):  # type: ignore[name-defined]
    __tablename__ = "refund_lines"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    refund_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("refunds.id"), nullable=False, index=True)
    sale_line_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sale_lines.id"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    
    refund: Mapped[RefundModel] = relationship("RefundModel", back_populates="lines")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_refundline_qty_positive"),
    )
