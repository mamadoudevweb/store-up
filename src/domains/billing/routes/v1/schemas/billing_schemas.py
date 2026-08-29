"""Billing Pydantic schemas for request/response serialization."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator


# ---------------------------------------------------------------------------
# PaymentMethod
# ---------------------------------------------------------------------------

class PaymentMethodCreate(BaseModel):
    name: str
    processor_key: str
    is_active: bool = False


class PaymentMethodResponse(BaseModel):
    id: uuid.UUID
    name: str
    processor_key: str
    is_active: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Payment
# ---------------------------------------------------------------------------

class PaymentResponse(BaseModel):
    id: uuid.UUID
    sale_id: uuid.UUID
    attempt_number: int
    payment_method_id: uuid.UUID
    processor_key: str
    amount: int
    status: str
    processor_reference: str | None = None
    failure_reason: str | None = None
    created_at: datetime
    resolved_at: datetime | None = None

    model_config = {"from_attributes": True}


class RetryPaymentRequest(BaseModel):
    payment_method_id: uuid.UUID | None = None


# ---------------------------------------------------------------------------
# RefundSettlement
# ---------------------------------------------------------------------------

class RefundSettlementResponse(BaseModel):
    id: uuid.UUID
    refund_id: uuid.UUID
    payment_id: uuid.UUID
    attempt_number: int
    amount: int
    processor_key: str
    status: str
    processor_reference: str | None = None
    failure_reason: str | None = None
    created_at: datetime
    resolved_at: datetime | None = None

    model_config = {"from_attributes": True}
