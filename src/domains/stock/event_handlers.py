"""Stock event handlers."""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.events.dispatcher import EventDispatcher
from src.domains.catalog.events import VariantCreated
from src.domains.sale.events import SaleCreated, SaleFailed, RefundCompleted
from src.domains.billing.entities.events import PaymentCaptured
from src.domains.stock.entities.stock_item import StockItem
from src.domains.stock.entities.enums import ReferenceType, StockMovementReason

if TYPE_CHECKING:
    from src.app.domain_service import DomainService


def register(dispatcher: EventDispatcher, domain_service: DomainService) -> None:
    def on_variant_created(event: VariantCreated) -> None:
        """Automatically create a 0-stock item when a new variant is created."""
        with domain_service.stock.item._uow_factory() as uow:
            item = StockItem.create(variant_id=event.variant_id, low_stock_threshold=0)
            uow.stock_items.add(item)
            uow.track(item)

    def on_sale_created(event: SaleCreated) -> None:
        from src.core.services.system_account import SystemAccount
        from src.domains.stock.exceptions import InsufficientStockError
        from src.domains.stock.events import StockReservationFailed
        import logging
        
        logger = logging.getLogger(__name__)

        try:
            sale_result = domain_service.sale.sale._uow_factory().__enter__()
            sale = sale_result.sales.get(event.sale_id)
            sale_result.__exit__(None, None, None)
        except Exception:
            logger.exception("Failed to lookup sale lines")
            return
            
        if not sale:
            return

        for line in sale.lines:
            try:
                # Use reserve_stock which emits StockReserved event
                domain_service.stock.item.reserve_stock(
                    SystemAccount(),
                    variant_id=line.variant_id,
                    quantity=line.quantity,
                    reference_type=ReferenceType.SALE,
                    reference_id=str(event.sale_id)
                )
            except InsufficientStockError as e:
                dispatcher.dispatch(StockReservationFailed(
                    variant_id=line.variant_id,
                    quantity=line.quantity,
                    reference_type=ReferenceType.SALE,
                    reference_id=str(event.sale_id),
                    reason=str(e)
                ))
                break

    def on_sale_failed(event: SaleFailed) -> None:
        from src.core.services.system_account import SystemAccount
        try:
            sale_result = domain_service.sale.sale._uow_factory().__enter__()
            sale = sale_result.sales.get(event.sale_id)
            sale_result.__exit__(None, None, None)
        except Exception:
            return
            
        if not sale:
            return
            
        for line in sale.lines:
            try:
                domain_service.stock.item.release_stock(
                    SystemAccount(),
                    variant_id=line.variant_id,
                    quantity=line.quantity,
                    reference_type=ReferenceType.SALE,
                    reference_id=str(event.sale_id)
                )
            except Exception:
                pass
                
    def on_payment_captured(event: PaymentCaptured) -> None:
        from src.core.services.system_account import SystemAccount
        try:
            sale_result = domain_service.sale.sale._uow_factory().__enter__()
            sale = sale_result.sales.get(event.sale_id)
            sale_result.__exit__(None, None, None)
        except Exception:
            return
            
        if not sale:
            return
            
        for line in sale.lines:
            try:
                domain_service.stock.item.ship_stock(
                    SystemAccount(),
                    variant_id=line.variant_id,
                    quantity=line.quantity,
                    reference_type=ReferenceType.SALE,
                    reference_id=str(event.sale_id)
                )
            except Exception:
                pass
                
    def on_refund_completed(event: RefundCompleted) -> None:
        from src.core.services.system_account import SystemAccount
        import uuid
        
        for line in event.lines:
            try:
                domain_service.stock.item.adjust_stock(
                    SystemAccount(),
                    variant_id=uuid.UUID(str(line["variant_id"])),
                    quantity_change=line["quantity"],
                    reason=StockMovementReason.RETURN,
                    reference_type=ReferenceType.SALE,
                    reference_id=str(event.sale_id)
                )
            except Exception:
                pass

    dispatcher.subscribe(VariantCreated, on_variant_created)
    dispatcher.subscribe(SaleCreated, on_sale_created)
    dispatcher.subscribe(SaleFailed, on_sale_failed)
    dispatcher.subscribe(PaymentCaptured, on_payment_captured)
    dispatcher.subscribe(RefundCompleted, on_refund_completed)
