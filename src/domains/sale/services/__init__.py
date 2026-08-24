from typing import Any

from src.domains.sale.services.sale_service import SaleService
from src.domains.sale.services.refund_service import RefundService


class SaleDomainService:
    """Aggregates sale entity services."""
    
    def __init__(self, **entity_services: Any) -> None:
        self.__dict__.update(entity_services)


__all__ = [
    "SaleService",
    "RefundService",
    "SaleDomainService",
]
