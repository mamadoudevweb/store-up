"""Billing domain enums."""
from enum import Enum


class PaymentStatus(str, Enum):
    """Status of a single Payment attempt row."""
    PENDING = "pending"
    CAPTURED = "captured"
    FAILED = "failed"


class RefundSettlementStatus(str, Enum):
    """Status of a single RefundSettlement attempt row."""
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
