"""Billing domain event handlers.

Billing reacts to:
  StockReserved    → attempt payment capture (attempt 1)
  RefundRequested  → attempt refund settlement

Billing emits (via entity domain events, dispatched by UoW after commit):
  PaymentCaptured, PaymentFailed, RefundProcessed, RefundFailed
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.core.events.dispatcher import EventDispatcher
from src.core.services.system_account import SystemAccount
from src.domains.stock.events import StockReserved
from src.domains.sale.events import RefundRequested

if TYPE_CHECKING:
    from src.app.domain_service import DomainService

logger = logging.getLogger(__name__)


def register(dispatcher: EventDispatcher, domain_service: "DomainService") -> None:
    """Register billing domain event subscriptions."""

    def on_stock_reserved(event: StockReserved) -> None:
        """StockReserved → capture(sale_id, payment_method_id, amount).

        Per event-catalog.md §2.2: Billing is invoked ONLY after a successful
        stock reservation. The sale_id is carried in event.reference_id.
        The payment_method_id and amount are looked up from the Sale entity via
        the Sale service — we read from the Sale domain's data, but through the
        sale service (read-only lookup, not a mutation).
        """
        import uuid

        # reference_id is the sale_id, stored as a string per StockReserved.
        if event.reference_id is None:
            logger.warning("StockReserved event missing reference_id, skipping billing.")
            return

        from src.domains.stock.entities.enums import ReferenceType
        if event.reference_type != ReferenceType.SALE:
            return  # Not a sale reservation — Billing doesn't care.

        sale_id = uuid.UUID(str(event.reference_id))

        # Look up the sale to get amount and payment_method_id.
        # This is a cross-domain read — acceptable per the architecture because
        # we're only reading, not writing, and we use the service layer.
        try:
            sale_result = domain_service.sale.sale._uow_factory().__enter__()
            sale = sale_result.sales.get(sale_id)
            sale_result.__exit__(None, None, None)
        except Exception:
            # If lookup fails we can't proceed — log and return.
            logger.exception("Failed to look up sale=%s for billing capture.", sale_id)
            return

        if sale is None:
            logger.warning("StockReserved: sale=%s not found, skipping capture.", sale_id)
            return

        idempotency_key = f"capture:{sale_id}:1"

        try:
            domain_service.billing.payment.capture(
                actor=SystemAccount(),
                sale_id=sale_id,
                payment_method_id=sale.payment_method_id,
                amount=sale.total,
                idempotency_key=idempotency_key,
            )
        except Exception:
            logger.exception("Billing capture failed for sale=%s.", sale_id)

    def on_refund_requested(event: RefundRequested) -> None:
        """RefundRequested → settle_refund(refund_id, payment_id, amount).

        Resolves the original captured Payment for sale_id, then settles.
        Billing trusts the event's amount as the authoritative total (spec §6.3).
        """
        import uuid

        try:
            # Find the captured payment for this sale.
            with domain_service.billing.payment._uow_factory() as uow:
                payment = uow.payments.captured_payment_for_sale(event.sale_id)

            if payment is None:
                logger.warning(
                    "RefundRequested: no captured payment for sale=%s, skipping settlement.",
                    event.sale_id,
                )
                return

            domain_service.billing.payment.settle_refund(
                actor=SystemAccount(),
                refund_id=event.refund_id,
                payment_id=payment.id,
                amount=event.amount,
                expected_total=event.amount,
            )
        except Exception:
            logger.exception(
                "Billing settle_refund failed for refund=%s.", event.refund_id
            )

    dispatcher.subscribe(StockReserved, on_stock_reserved)
    dispatcher.subscribe(RefundRequested, on_refund_requested)
