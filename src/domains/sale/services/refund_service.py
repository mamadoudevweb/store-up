import uuid

from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.result import ServiceResult
from src.domains.sale.entities.refund import Refund
from src.domains.sale.entities.refund_line import RefundLine
from src.domains.sale.exceptions import SaleNotFoundError, RefundNotFoundError, SaleLineNotFoundError, RefundQuantityExceededError


class RefundService(BaseService):
    def request_refund(
        self,
        account: SupportsPermissionCheck,
        sale_id: uuid.UUID,
        processed_by: uuid.UUID,
        reason: str,
        lines_data: list[dict],
    ) -> ServiceResult[Refund]:
        """
        Creates a refund for a completed sale.
        """
        self._authorize(account, "sale", "refund", "create")
        
        with self._uow_factory() as uow:
            sale = getattr(uow, "sales").get(sale_id)
            if not sale:
                raise SaleNotFoundError()

            refund_lines = []
            amount = 0
            
            for line_data in lines_data:
                sale_line_id = line_data["sale_line_id"]
                quantity = line_data["quantity"]
                
                sale_line = next((sl for sl in sale.lines if str(sl.id) == str(sale_line_id)), None)
                if not sale_line:
                    raise SaleLineNotFoundError(f"Sale line {sale_line_id} not found in sale {sale_id}")
                
                # We validate here but we DO NOT mutate sale_line.refunded_quantity directly here.
                # Sale service will do it upon reacting to RefundRequested.
                if sale_line.refunded_quantity + quantity > sale_line.quantity:
                    raise RefundQuantityExceededError(f"Cannot refund more than sold for line {sale_line_id}")
                    
                refund_lines.append(
                    RefundLine.create(
                        refund_id=uuid.uuid4(),
                        sale_line_id=sale_line.id,
                        quantity=quantity,
                    )
                )

                amount += sale_line.unit_price * quantity

            refund = Refund.create(
                sale_id=sale_id,
                processed_by=processed_by,
                reason=reason,
                lines=refund_lines,
            )
            
            from src.domains.sale.events import RefundRequested
            refund.register_event(RefundRequested(
                refund_id=refund.id,
                sale_id=sale_id,
                amount=amount,
                lines_data=lines_data
            ))
            
            getattr(uow, "refunds").add(refund)
            uow.track(refund)
            uow.commit()
            
            return ServiceResult(data=refund)

    def complete_refund(self, account: SupportsPermissionCheck, refund_id: uuid.UUID) -> ServiceResult[Refund]:
        """Called by event handler when refund payment is successful."""
        self._authorize(account, "sale", "refund", "update")
        with self._uow_factory() as uow:
            refund = getattr(uow, "refunds").get(refund_id)
            if not refund:
                raise RefundNotFoundError()
                
            refund.mark_processed()
            getattr(uow, "refunds").update(refund)
            uow.commit()
            return ServiceResult(data=refund)

    def fail_refund(self, account: SupportsPermissionCheck, refund_id: uuid.UUID) -> ServiceResult[Refund]:
        """Called by event handler when refund payment fails."""
        self._authorize(account, "sale", "refund", "update")
        with self._uow_factory() as uow:
            refund = getattr(uow, "refunds").get(refund_id)
            if not refund:
                raise RefundNotFoundError()
                
            refund.mark_failed()
            getattr(uow, "refunds").update(refund)
            uow.commit()
            return ServiceResult(data=refund)
