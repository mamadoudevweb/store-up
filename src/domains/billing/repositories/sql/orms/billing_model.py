"""Billing SQLAlchemy ORM models.

Key constraints from spec §4.2 / §4.3:
- Partial unique index: at most one Payment row per sale_id with status='pending'.
- Same scoped to refund_id for RefundSettlement.
- No cardholder data fields — processor_reference is an opaque token only.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.app.extensions import db


class PaymentMethodModel(db.Model):  # type: ignore[name-defined]
    __tablename__ = "payment_methods"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    processor_key: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        CheckConstraint("length(name) > 0", name="chk_pm_name_nonempty"),
        CheckConstraint("length(processor_key) > 0", name="chk_pm_processor_key_nonempty"),
    )


class PaymentModel(db.Model):  # type: ignore[name-defined]
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    sale_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_method_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    # Snapshotted at creation — never re-read from payment_methods.
    processor_key: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # Opaque processor token — never raw card data (spec §9.1).
    processor_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    failure_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("sale_id", "attempt_number", name="uq_payment_sale_attempt"),
        CheckConstraint("amount > 0", name="chk_payment_amount_positive"),
        CheckConstraint(
            "status IN ('pending', 'captured', 'failed')",
            name="chk_payment_status",
        ),
        # Partial unique index: only one pending row per sale_id at a time.
        # Enforces concurrency safety at DB level (spec §7.1) for SQLite/Postgres.
        Index(
            "ix_payments_sale_pending",
            "sale_id",
            unique=True,
            sqlite_where=db.text("status = 'pending'"),
        ),
    )


class RefundSettlementModel(db.Model):  # type: ignore[name-defined]
    __tablename__ = "refund_settlements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Sale's Refund.id — copied via event, not a live cross-domain FK.
    refund_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    # FK → payments.id (the attempt that originally captured).
    payment_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    processor_key: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    processor_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("refund_id", "attempt_number", name="uq_settlement_refund_attempt"),
        CheckConstraint("amount > 0", name="chk_settlement_amount_positive"),
        CheckConstraint(
            "status IN ('pending', 'processed', 'failed')",
            name="chk_settlement_status",
        ),
        # Partial unique index: only one pending settlement per refund_id at a time.
        Index(
            "ix_settlements_refund_pending",
            "refund_id",
            unique=True,
            sqlite_where=db.text("status = 'pending'"),
        ),
    )
