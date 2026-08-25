from typing import Any

from src.domains.sale.services.sale_service import SaleService
from src.domains.sale.services.refund_service import RefundService


class SaleDomainService:
    """Aggregates sale entity services."""
    
    sale: SaleService
    refund: RefundService
    
    def __init__(self, **entity_services: Any) -> None:
        """
        Initialize the domain service with dynamically supplied entity services.
        
        Parameters:
            entity_services (Any): Named services to attach to the domain service.
        """
        self.__dict__.update(entity_services)


__all__ = [
    "SaleService",
    "RefundService",
    "SaleDomainService",
]
