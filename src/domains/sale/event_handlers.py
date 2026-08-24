from src.core.events.dispatcher import EventDispatcher
from src.app.domain_service import DomainService
from src.domains.sale.events import SaleReturned, RefundRequested

from src.core.services.system_account import SystemAccount

def register(dispatcher: EventDispatcher, domain_service: DomainService) -> None:
    """Register sale domain event handlers."""
    
    def on_refund_requested(event: RefundRequested) -> None:
        domain_service.sale.sale.process_refund(
            SystemAccount(),
            sale_id=event.sale_id,
            refund_id=event.refund_id,
            lines_data=event.lines_data,
            amount=event.amount
        )
        
    def on_sale_returned(event: SaleReturned) -> None:
        domain_service.sale.refund.complete_refund(SystemAccount(), event.refund_id)
        
    dispatcher.subscribe(RefundRequested, on_refund_requested)
    dispatcher.subscribe(SaleReturned, on_sale_returned)
