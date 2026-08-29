"""Pluggable processor interface and registry.

spec §4 — PaymentProcessor (pluggable interface, code not schema):
- PROCESSOR_REGISTRY maps processor_key → implementation class.
- CashProcessor is the only real implementation today.
- Adding Card/Mobile = add a new class + one registry entry, zero changes here.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Literal
import uuid


@dataclass(frozen=True)
class ProcessorResult:
    """Result returned by any PaymentProcessor call.

    status:
      - "captured"  — money moved, capture succeeded
      - "processed" — refund completed
      - "failed"    — processor declined / error
      - "pending"   — outcome unknown (timeout / no response)
    """
    status: Literal["captured", "processed", "failed", "pending"]
    processor_reference: str | None = None
    failure_reason: str | None = None


class PaymentProcessor(ABC):
    """Abstract base every processor must implement."""
    key: ClassVar[str]

    @abstractmethod
    def capture(
        self,
        *,
        amount: int,
        payment_id: uuid.UUID,
    ) -> ProcessorResult:
        """Attempt to charge `amount`. Return a ProcessorResult."""
        ...

    @abstractmethod
    def refund(
        self,
        *,
        amount: int,
        original_reference: str | None,
        refund_id: uuid.UUID,
    ) -> ProcessorResult:
        """Attempt to reverse a prior capture. Return a ProcessorResult."""
        ...


# ---------------------------------------------------------------------------
# Registry — the single source of truth for processor_key → class mapping.
# At startup, every active PaymentMethod.processor_key must be present here.
# ---------------------------------------------------------------------------

from src.domains.billing.processors.cash_processor import CashProcessor  # noqa: E402

PROCESSOR_REGISTRY: dict[str, type[PaymentProcessor]] = {
    "cash_manual": CashProcessor,
    # "card_gateway_x": CardGatewayProcessor,  — added later; zero code changes here
}

__all__ = ["ProcessorResult", "PaymentProcessor", "PROCESSOR_REGISTRY"]
