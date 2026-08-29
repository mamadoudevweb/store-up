"""Billing domain repository filters."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.core.entities.pagination import EntityFilter
from src.domains.billing.entities.enums import PaymentStatus, RefundSettlementStatus


@dataclass(kw_only=True)
class PaymentMethodFilter(EntityFilter):
    id: uuid.UUID | None = None
    name: str | None = None
    processor_key: str | None = None
    is_active: bool | None = None


@dataclass(kw_only=True)
class PaymentFilter(EntityFilter):
    id: uuid.UUID | None = None
    sale_id: uuid.UUID | None = None
    status: PaymentStatus | None = None
    idempotency_key: str | None = None


@dataclass(kw_only=True)
class RefundSettlementFilter(EntityFilter):
    id: uuid.UUID | None = None
    refund_id: uuid.UUID | None = None
    payment_id: uuid.UUID | None = None
    status: RefundSettlementStatus | None = None
