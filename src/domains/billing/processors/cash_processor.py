"""CashProcessor — the only concrete processor for now.

capture() returns captured immediately (no external call, cash is immediate).
refund() returns processed immediately (cash refund is manual/physical).
processor_reference is None for both — there's nothing external to reference.
"""
from __future__ import annotations

import uuid
from typing import ClassVar


class CashProcessor:
    """Handles cash payments. No external gateway, no async, no failure modes."""
    key: ClassVar[str] = "cash_manual"

    def capture(
        self,
        *,
        amount: int,
        payment_id: uuid.UUID,
    ) -> "ProcessorResult":  # type: ignore[name-defined]  # avoid circular at class body
        from src.domains.billing.processors import ProcessorResult
        return ProcessorResult(
            status="captured",
            processor_reference=None,
            failure_reason=None,
        )

    def refund(
        self,
        *,
        amount: int,
        original_reference: str | None,
        refund_id: uuid.UUID,
    ) -> "ProcessorResult":  # type: ignore[name-defined]
        from src.domains.billing.processors import ProcessorResult
        return ProcessorResult(
            status="processed",
            processor_reference=None,
            failure_reason=None,
        )
