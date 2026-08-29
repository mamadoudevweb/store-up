"""Billing domain events — outbound event contracts per billing-domain-spec.md §8."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.core.entities.events import DomainEvent


@dataclass(kw_only=True, frozen=True)
class PaymentCaptured(DomainEvent):
    """Emitted when a Payment attempt reaches the captured terminal state."""
    sale_id: uuid.UUID
    payment_id: uuid.UUID
    attempt_number: int
    event_name: str = "payment_captured"
    event_version: int = 1


@dataclass(kw_only=True, frozen=True)
class PaymentFailed(DomainEvent):
    """Emitted when a Payment attempt reaches the failed terminal state."""
    sale_id: uuid.UUID
    payment_id: uuid.UUID
    attempt_number: int
    reason: str
    event_name: str = "payment_failed"
    event_version: int = 1


@dataclass(kw_only=True, frozen=True)
class RefundProcessed(DomainEvent):
    """Emitted when a RefundSettlement attempt reaches the processed terminal state."""
    refund_id: uuid.UUID
    settlement_id: uuid.UUID
    event_name: str = "refund_processed"
    event_version: int = 1


@dataclass(kw_only=True, frozen=True)
class RefundFailed(DomainEvent):
    """Emitted when a RefundSettlement attempt reaches the failed terminal state."""
    refund_id: uuid.UUID
    settlement_id: uuid.UUID
    reason: str
    event_name: str = "refund_failed"
    event_version: int = 1
