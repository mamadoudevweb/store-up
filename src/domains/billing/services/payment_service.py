"""PaymentService — implements the three core billing operations.

Contracts from billing-domain-spec.md §6:
  capture()       — §6.1: attempt 1, precondition = no existing Payment for sale_id
  retry_payment() — §6.2: precondition = latest Payment is failed (not pending)
  settle_refund() — §6.3: resolves original Payment → same processor_key

Concurrency + idempotency guards (spec §7):
  §7.1: partial unique index on (sale_id) WHERE status='pending' prevents double-capture
  §7.2: unique idempotency_key prevents duplicate-delivery from creating a second row
  §7.3: attempt_number computed via MAX+1 inside the transaction (safe enough with the
        unique constraint as final guard)
"""
from __future__ import annotations

import logging
import uuid

from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.result import ServiceResult
from src.domains.billing.entities.payment import Payment
from src.domains.billing.entities.refund_settlement import RefundSettlement
from src.domains.billing.entities.enums import PaymentStatus, RefundSettlementStatus
from src.domains.billing.exceptions import (
    BillingDuplicateAttemptError,
    BillingRetryOnUnresolvedAttemptError,
    BillingUnsupportedProcessorError,
    BillingOverRefundError,
    BillingSettlementNotFoundError,
    BillingPaymentNotFoundError,
    BillingPaymentMethodNotFoundError,
)

logger = logging.getLogger(__name__)


class PaymentService(BaseService):
    # ------------------------------------------------------------------
    # capture() — spec §6.1
    # ------------------------------------------------------------------
    def capture(
        self,
        actor: SupportsPermissionCheck,
        sale_id: uuid.UUID,
        payment_method_id: uuid.UUID,
        amount: int,
        idempotency_key: str,
    ) -> ServiceResult[Payment]:
        """Create attempt 1 for a sale. Raises if a Payment row already exists."""
        self._authorize(actor, "billing", "payment", "create")

        with self._uow_factory() as uow:
            # Idempotency guard first — if this exact key was already processed,
            # return the existing row rather than erroring (spec §7.2).
            existing_by_key = uow.payments.get_by_idempotency_key(idempotency_key)
            if existing_by_key is not None:
                logger.info(
                    "Idempotent capture: key=%s already resolved to payment=%s",
                    idempotency_key,
                    existing_by_key.id,
                )
                return ServiceResult(data=existing_by_key)

            # Precondition: no existing payment for this sale (spec §6.1).
            existing = uow.payments.latest_for_sale(sale_id)
            if existing is not None:
                raise BillingDuplicateAttemptError(sale_id=str(sale_id))

            # Resolve payment method and snapshot processor_key.
            pm = uow.payment_methods.get(payment_method_id)
            if pm is None:
                raise BillingPaymentMethodNotFoundError()

            processor_key = pm.processor_key
            self._validate_processor_key(processor_key)

            payment = Payment.create(
                sale_id=sale_id,
                attempt_number=1,
                payment_method_id=payment_method_id,
                processor_key=processor_key,
                amount=amount,
                idempotency_key=idempotency_key,
            )
            uow.payments.add(payment)
            # Flush so the row is visible in the same tx (needed for partial unique index).
            uow.payments._session.flush()

        # Processor call is outside the UoW — row is persisted as pending first.
        # If the processor call raises or times out the row stays pending (spec §5.1 / §11.1).
        return self._invoke_processor_capture(
            sale_id=sale_id,
            payment=payment,
            processor_key=processor_key,
        )

    # ------------------------------------------------------------------
    # retry_payment() — spec §6.2
    # ------------------------------------------------------------------
    def retry_payment(
        self,
        actor: SupportsPermissionCheck,
        sale_id: uuid.UUID,
        payment_method_id: uuid.UUID | None = None,
    ) -> ServiceResult[Payment]:
        """Create a new payment attempt. Precondition: latest attempt is failed."""
        self._authorize(actor, "billing", "payment", "create")

        with self._uow_factory() as uow:
            latest = uow.payments.latest_for_sale(sale_id)
            if latest is None:
                raise BillingPaymentNotFoundError(sale_id=str(sale_id))

            if latest.status == PaymentStatus.PENDING:
                raise BillingRetryOnUnresolvedAttemptError(sale_id=str(sale_id))

            if latest.status == PaymentStatus.CAPTURED:
                raise BillingDuplicateAttemptError(
                    sale_id=str(sale_id),
                    message="Payment already captured for this sale.",
                )

            # Use provided payment_method_id or fall back to the previous attempt's.
            effective_pm_id = payment_method_id or latest.payment_method_id
            pm = uow.payment_methods.get(effective_pm_id)
            if pm is None:
                raise BillingPaymentMethodNotFoundError()

            processor_key = pm.processor_key
            self._validate_processor_key(processor_key)

            attempt_number = uow.payments.next_attempt_number(sale_id)
            idempotency_key = f"{sale_id}:{attempt_number}"

            payment = Payment.create(
                sale_id=sale_id,
                attempt_number=attempt_number,
                payment_method_id=effective_pm_id,
                processor_key=processor_key,
                amount=latest.amount,
                idempotency_key=idempotency_key,
            )
            uow.payments.add(payment)
            uow.payments._session.flush()

        return self._invoke_processor_capture(
            sale_id=sale_id,
            payment=payment,
            processor_key=processor_key,
        )

    # ------------------------------------------------------------------
    # settle_refund() — spec §6.3
    # ------------------------------------------------------------------
    def settle_refund(
        self,
        actor: SupportsPermissionCheck,
        refund_id: uuid.UUID,
        payment_id: uuid.UUID,
        amount: int,
        expected_total: int,
    ) -> ServiceResult[RefundSettlement]:
        """Create a refund settlement attempt against the original payment's processor.

        `expected_total` is the full refund amount from the triggering event payload
        (Billing trusts the event, never queries Sale — spec §6.3).
        """
        self._authorize(actor, "billing", "refund_settlement", "create")

        with self._uow_factory() as uow:
            # Resolve the original captured payment.
            payment = uow.payments.get(payment_id)
            if payment is None:
                raise BillingPaymentNotFoundError(payment_id=str(payment_id))

            processor_key = payment.processor_key
            self._validate_processor_key(processor_key)

            # Over-refund guard (spec §6.3).
            already_settled = uow.refund_settlements.total_settled_for_refund(refund_id)
            if already_settled + amount > expected_total:
                raise BillingOverRefundError(
                    refund_id=str(refund_id),
                    requested=amount,
                    already_settled=already_settled,
                    max_allowed=expected_total,
                )

            attempt_number = uow.refund_settlements.next_attempt_number(refund_id)

            settlement = RefundSettlement.create(
                refund_id=refund_id,
                payment_id=payment_id,
                attempt_number=attempt_number,
                amount=amount,
                processor_key=processor_key,
            )
            uow.refund_settlements.add(settlement)
            uow.refund_settlements._session.flush()

        return self._invoke_processor_refund(
            refund_id=refund_id,
            settlement=settlement,
            original_reference=payment.processor_reference,
            processor_key=processor_key,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def list_for_sale(
        self,
        actor: SupportsPermissionCheck,
        sale_id: uuid.UUID,
    ) -> ServiceResult[list[Payment]]:
        """List all payment attempts for a given sale."""
        self._authorize(actor, "billing", "payment", "read")

        with self._uow_factory() as uow:
            payments = uow.payments.list_for_sale(sale_id)
            return ServiceResult(data=payments)

    @staticmethod
    def _validate_processor_key(processor_key: str) -> None:
        from src.domains.billing.processors import PROCESSOR_REGISTRY
        if processor_key not in PROCESSOR_REGISTRY:
            raise BillingUnsupportedProcessorError(processor_key=processor_key)

    def _invoke_processor_capture(
        self,
        sale_id: uuid.UUID,
        payment: Payment,
        processor_key: str,
    ) -> ServiceResult[Payment]:
        """Call processor.capture() and resolve the payment row.

        On timeout / unknown outcome: row stays pending (spec §5.1 / §11.1).
        """
        from src.domains.billing.processors import PROCESSOR_REGISTRY, ProcessorResult

        processor_cls = PROCESSOR_REGISTRY[processor_key]
        processor = processor_cls()

        try:
            result: ProcessorResult = processor.capture(
                amount=payment.amount,
                payment_id=payment.id,
            )
        except Exception as exc:
            # Timeout or network failure — row stays pending; do not mark failed.
            logger.warning(
                "Processor capture raised an exception for payment=%s; "
                "row stays pending. Error: %s",
                payment.id,
                exc,
            )
            return ServiceResult(data=payment)

        # Resolve terminal state.
        with self._uow_factory() as uow:
            live = uow.payments.get(payment.id)
            if live is None:
                logger.error("Payment row %s disappeared after creation.", payment.id)
                return ServiceResult(data=payment)

            if result.status == "captured":
                live.mark_captured(result.processor_reference)
            elif result.status == "failed":
                live.mark_failed(result.failure_reason or "processor declined")
            else:
                # pending / unknown — leave the row as-is
                return ServiceResult(data=live)

            uow.payments.update(live)
            uow.track(live)
            uow.commit()
        return ServiceResult(data=live)

    def _invoke_processor_refund(
        self,
        refund_id: uuid.UUID,
        settlement: RefundSettlement,
        original_reference: str | None,
        processor_key: str,
    ) -> ServiceResult[RefundSettlement]:
        """Call processor.refund() and resolve the settlement row."""
        from src.domains.billing.processors import PROCESSOR_REGISTRY, ProcessorResult

        processor_cls = PROCESSOR_REGISTRY[processor_key]
        processor = processor_cls()

        try:
            result: ProcessorResult = processor.refund(
                amount=settlement.amount,
                original_reference=original_reference,
                refund_id=refund_id,
            )
        except Exception as exc:
            logger.warning(
                "Processor refund raised an exception for settlement=%s; "
                "row stays pending. Error: %s",
                settlement.id,
                exc,
            )
            return ServiceResult(data=settlement)

        with self._uow_factory() as uow:
            live = uow.refund_settlements.get(settlement.id)
            if live is None:
                logger.error(
                    "RefundSettlement row %s disappeared after creation.", settlement.id
                )
                return ServiceResult(data=settlement)

            if result.status == "processed":
                live.mark_processed(result.processor_reference)
            elif result.status == "failed":
                live.mark_failed(result.failure_reason or "processor declined")
            else:
                return ServiceResult(data=live)

            uow.refund_settlements.update(live)
            uow.track(live)
            uow.commit()
        return ServiceResult(data=live)
