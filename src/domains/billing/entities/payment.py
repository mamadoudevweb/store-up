"""Payment entity — append-only attempts ledger, 1:N with Sale.

Business rules from billing-domain-spec.md §4.2 and §5.1:
- Rows are immutable once terminal (captured | failed).
- Retry creates a new row — never mutates an existing one.
- A row whose processor call timed out stays pending until reconciliation resolves it.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from src.core.entities.base_entity import BaseEntity
from src.domains.billing.entities.enums import PaymentStatus
from src.domains.billing.entities.events import PaymentCaptured, PaymentFailed


@dataclass(kw_only=True)
class Payment(BaseEntity[uuid.UUID]):
    """A single payment attempt against a processor."""
    id: uuid.UUID
    sale_id: uuid.UUID
    attempt_number: int
    payment_method_id: uuid.UUID
    # Snapshotted at creation — never re-read from PaymentMethod after this.
    processor_key: str
    amount: int
    status: PaymentStatus
    # Populated only on captured; never contains cardholder data (spec §9.1).
    processor_reference: str | None
    # Unique per row — guards duplicate-delivery (spec §7.2).
    idempotency_key: str
    failure_reason: str | None
    created_at: datetime
    resolved_at: datetime | None

    @classmethod
    def create(
        cls,
        sale_id: uuid.UUID,
        attempt_number: int,
        payment_method_id: uuid.UUID,
        processor_key: str,
        amount: int,
        idempotency_key: str,
    ) -> "Payment":
        if amount <= 0:
            raise ValueError(f"Payment amount must be > 0, got {amount}")
        return cls(
            id=uuid.uuid4(),
            sale_id=sale_id,
            attempt_number=attempt_number,
            payment_method_id=payment_method_id,
            processor_key=processor_key,
            amount=amount,
            status=PaymentStatus.PENDING,
            processor_reference=None,
            idempotency_key=idempotency_key,
            failure_reason=None,
            created_at=datetime.now(timezone.utc),
            resolved_at=None,
        )

    # ------------------------------------------------------------------
    # State transitions — only called from PaymentService after a processor call
    # ------------------------------------------------------------------

    def mark_captured(self, processor_reference: str | None) -> None:
        """Transition to the captured terminal state and register the domain event."""
        if self.status != PaymentStatus.PENDING:
            raise ValueError(
                f"Cannot capture a payment in state {self.status.value!r}"
            )
        self.status = PaymentStatus.CAPTURED
        self.processor_reference = processor_reference
        self.resolved_at = datetime.now(timezone.utc)
        self.register_event(
            PaymentCaptured(
                sale_id=self.sale_id,
                payment_id=self.id,
                attempt_number=self.attempt_number,
            )
        )

    def mark_failed(self, failure_reason: str) -> None:
        """Transition to the failed terminal state and register the domain event."""
        if self.status != PaymentStatus.PENDING:
            raise ValueError(
                f"Cannot fail a payment in state {self.status.value!r}"
            )
        self.status = PaymentStatus.FAILED
        self.failure_reason = failure_reason
        self.resolved_at = datetime.now(timezone.utc)
        self.register_event(
            PaymentFailed(
                sale_id=self.sale_id,
                payment_id=self.id,
                attempt_number=self.attempt_number,
                reason=failure_reason,
            )
        )
