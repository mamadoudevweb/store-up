"""Billing domain exceptions — error code prefix: BILLING_.

Per architecture rule: each subclass of AppError is auto-registered by
AppError.__init_subclass__. No manual registry maintenance needed.
"""
from src.core.services.errors import (
    AppError,
    ConflictError,
    NotFoundError,
    ValidationError,
)


class BillingDuplicateAttemptError(ConflictError):
    """capture() called for a sale_id that already has a Payment row."""
    code = "BILLING_DUPLICATE_ATTEMPT"
    message = "A payment capture for this sale already exists. Use retry_payment() for subsequent attempts."


class BillingRetryOnUnresolvedAttemptError(ConflictError):
    """retry_payment() called while the most recent attempt is still pending."""
    code = "BILLING_RETRY_ON_UNRESOLVED_ATTEMPT"
    message = "Cannot create a new payment attempt while the current one is still pending."


class BillingUnsupportedProcessorError(ValidationError):
    """processor_key not found in PROCESSOR_REGISTRY."""
    code = "BILLING_UNSUPPORTED_PROCESSOR"
    message = "The requested processor is not registered."


class BillingProcessorTimeoutError(AppError):
    """A capture/refund call exceeded its configured timeout."""
    code = "BILLING_PROCESSOR_TIMEOUT"
    status_code = 504
    message = "The payment processor did not respond in time. Outcome is unknown."


class BillingOverRefundError(ValidationError):
    """settle_refund amount would exceed the remaining unsettled amount."""
    code = "BILLING_OVER_REFUND"
    message = "The requested refund amount exceeds the remaining unsettled amount."


class BillingSettlementNotFoundError(NotFoundError):
    """Manual retry referencing a RefundSettlement/refund_id that doesn't exist."""
    code = "BILLING_SETTLEMENT_NOT_FOUND"
    message = "No refund settlement found for the given identifier."


class BillingPaymentNotFoundError(NotFoundError):
    """No payment found for a sale_id that should have one."""
    code = "BILLING_PAYMENT_NOT_FOUND"
    message = "No payment found for this sale."


class BillingPaymentMethodNotFoundError(NotFoundError):
    """PaymentMethod not found by id or name."""
    code = "BILLING_PAYMENT_METHOD_NOT_FOUND"
    message = "Payment method not found."
