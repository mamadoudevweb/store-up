"""RefundSettlement entity — append-only attempts ledger for refunds, 1:N with Refund.

Mirrors Payment's structure (spec §4.3 and §5.2).
Refund always goes through the same processor_key as the original capture.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from src.core.entities.base_entity import BaseEntity
from src.domains.billing.entities.enums import RefundSettlementStatus
from src.domains.billing.entities.events import RefundProcessed, RefundFailed


@dataclass(kw_only=True)
class RefundSettlement(BaseEntity[uuid.UUID]):
    """A single refund settlement attempt against a processor."""
    id: uuid.UUID
    # Sale's Refund.id, copied via event — not a live cross-domain FK.
    refund_id: uuid.UUID
    # The Payment attempt that originally captured; determines processor_key.
    payment_id: uuid.UUID
    attempt_number: int
    amount: int
    # Copied from the resolved Payment at creation time.
    processor_key: str
    status: RefundSettlementStatus
    processor_reference: str | None
    failure_reason: str | None
    created_at: datetime
    resolved_at: datetime | None

    @classmethod
    def create(
        cls,
        refund_id: uuid.UUID,
        payment_id: uuid.UUID,
        attempt_number: int,
        amount: int,
        processor_key: str,
    ) -> "RefundSettlement":
        if amount <= 0:
            raise ValueError(f"RefundSettlement amount must be > 0, got {amount}")
        return cls(
            id=uuid.uuid4(),
            refund_id=refund_id,
            payment_id=payment_id,
            attempt_number=attempt_number,
            amount=amount,
            processor_key=processor_key,
            status=RefundSettlementStatus.PENDING,
            processor_reference=None,
            failure_reason=None,
            created_at=datetime.now(timezone.utc),
            resolved_at=None,
        )

    def mark_processed(self, processor_reference: str | None) -> None:
        """Transition to the processed terminal state and register the domain event."""
        if self.status != RefundSettlementStatus.PENDING:
            raise ValueError(
                f"Cannot process a settlement in state {self.status.value!r}"
            )
        self.status = RefundSettlementStatus.PROCESSED
        self.processor_reference = processor_reference
        self.resolved_at = datetime.now(timezone.utc)
        self.register_event(
            RefundProcessed(
                refund_id=self.refund_id,
                settlement_id=self.id,
            )
        )

    def mark_failed(self, failure_reason: str) -> None:
        """Transition to the failed terminal state and register the domain event."""
        if self.status != RefundSettlementStatus.PENDING:
            raise ValueError(
                f"Cannot fail a settlement in state {self.status.value!r}"
            )
        self.status = RefundSettlementStatus.FAILED
        self.failure_reason = failure_reason
        self.resolved_at = datetime.now(timezone.utc)
        self.register_event(
            RefundFailed(
                refund_id=self.refund_id,
                settlement_id=self.id,
                reason=failure_reason,
            )
        )
