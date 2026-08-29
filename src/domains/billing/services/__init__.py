"""Billing domain service facade."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.domains.billing.services.payment_method_service import PaymentMethodService
    from src.domains.billing.services.payment_service import PaymentService


class BillingDomainService:
    """Aggregates billing entity services."""
    if TYPE_CHECKING:
        payment_method: PaymentMethodService
        payment: PaymentService

    def __init__(self, **entity_services: Any) -> None:
        self.__dict__.update(entity_services)


__all__ = ["BillingDomainService"]
