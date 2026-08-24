"""Sale SQLAlchemy models."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Integer, String, DateTime, func, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.extensions import db


class SaleModel(db.Model):  # type: ignore[name-defined]
    __tablename__ = "sales"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    number: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True, index=True)
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seller_account_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_method_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    
    discount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        server_default=func.now()
    )
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    lines: Mapped[list[SaleLineModel]] = relationship(
        "SaleLineModel", back_populates="sale", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'completed', 'failed', 'returned')", 
            name="chk_sale_status"
        ),
        CheckConstraint("discount >= 0", name="chk_sale_discount_positive"),
        CheckConstraint("subtotal >= 0", name="chk_sale_subtotal_positive"),
        CheckConstraint("total >= 0", name="chk_sale_total_positive"),
    )


class SaleLineModel(db.Model):  # type: ignore[name-defined]
    __tablename__ = "sale_lines"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    sale_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sales.id"), nullable=False, index=True)
    variant_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)
    discount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False)
    refunded_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    sale: Mapped[SaleModel] = relationship("SaleModel", back_populates="lines")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_saleline_qty_positive"),
        CheckConstraint("unit_price >= 0", name="chk_saleline_price_positive"),
        CheckConstraint("discount >= 0", name="chk_saleline_discount_positive"),
        CheckConstraint("subtotal >= 0", name="chk_saleline_subtotal_positive"),
        CheckConstraint("refunded_quantity >= 0", name="chk_saleline_refunded_positive"),
        CheckConstraint("refunded_quantity <= quantity", name="chk_saleline_refunded_max"),
    )
