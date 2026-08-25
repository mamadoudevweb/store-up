import uuid
import typing

from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.result import ServiceResult
from src.domains.sale.entities.refund import Refund
from src.domains.sale.entities.refund_line import RefundLine
from src.domains.sale.exceptions import SaleNotFoundError, RefundNotFoundError, SaleLineNotFoundError, RefundQuantityExceededError

if typing.TYPE_CHECKING:
    from src.domains.sale.entities.sale import Sale


class RefundService(BaseService):
    def _calc_total_refund(self, sale: "Sale", refund_qty_map: dict[uuid.UUID, int]) -> int:
        """
        Calculate the net refund amount for the specified sale line quantities.
        
        Parameters:
        	sale (Sale): Sale containing the lines and sale-level discount.
        	refund_qty_map (dict[uuid.UUID, int]): Mapping of sale line identifiers to refund quantities.
        
        Returns:
        	int: Net refund amount after applying the proportionally allocated sale-level discount.
        """
        total_net = sum(
            (line.unit_price - line.discount) * refund_qty_map.get(line.id, 0)
            for line in sale.lines
        )
        allocated = int((total_net / sale.subtotal) * sale.discount) if sale.subtotal > 0 else 0
        return total_net - allocated

    def request_refund(
        self,
        account: SupportsPermissionCheck,
        sale_id: uuid.UUID,
        processed_by: uuid.UUID,
        reason: str,
        lines_data: list[dict[str, typing.Any]],
    ) -> ServiceResult[Refund]:
        """
        Create a refund request for a completed sale.
        
        Parameters:
            processed_by (uuid.UUID): Identifier of the user processing the refund.
            reason (str): Explanation for the refund.
            lines_data (list[dict[str, typing.Any]]): Sale lines and quantities to refund.
        
        Returns:
            ServiceResult[Refund]: The created refund request.
        
        Raises:
            SaleNotFoundError: If the sale does not exist.
            SaleLineNotFoundError: If a requested sale line does not belong to the sale.
            RefundQuantityExceededError: If a requested quantity exceeds the quantity sold.
        """
        self._authorize(account, "sale", "refund", "create")
        
        with self._uow_factory() as uow:
            sale = getattr(uow, "sales").get(sale_id)
            if not sale:
                from src.domains.sale.exceptions import SaleNotFoundError
                raise SaleNotFoundError()
                
            before_map = {line.id: line.refunded_quantity for line in sale.lines}
            amount_before = self._calc_total_refund(sale, before_map)

            after_map = before_map.copy()
            refund_lines = []
            
            aggregated_requests: dict[uuid.UUID, int] = {}
            for line_data in lines_data:
                sale_line_id = uuid.UUID(str(line_data["sale_line_id"]))
                aggregated_requests[sale_line_id] = aggregated_requests.get(sale_line_id, 0) + line_data["quantity"]
            
            for sale_line_id, quantity in aggregated_requests.items():
                sale_line = next((sl for sl in sale.lines if sl.id == sale_line_id), None)
                if not sale_line:
                    raise SaleLineNotFoundError(f"Sale line {sale_line_id} not found in sale {sale_id}")
                
                # We validate here but we DO NOT mutate sale_line.refunded_quantity directly here.
                # Sale service will do it upon reacting to RefundRequested.
                if sale_line.refunded_quantity + quantity > sale_line.quantity:
                    raise RefundQuantityExceededError(f"Cannot refund more than sold for line {sale_line_id}")
                    
                after_map[sale_line_id] += quantity
                refund_lines.append(
                    RefundLine.create(
                        refund_id=uuid.uuid4(),
                        sale_line_id=sale_line.id,
                        quantity=quantity,
                    )
                )

            amount_after = self._calc_total_refund(sale, after_map)
            amount = amount_after - amount_before

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
        """
        Mark a refund as successfully processed.
        
        Parameters:
            refund_id (uuid.UUID): Identifier of the refund to complete.
        
        Returns:
            ServiceResult[Refund]: The processed refund.
        
        Raises:
            RefundNotFoundError: If the specified refund does not exist.
        """
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
        """
        Record a failed refund payment.
        
        Parameters:
        	refund_id (uuid.UUID): Identifier of the refund to mark as failed.
        
        Returns:
        	ServiceResult[Refund]: The updated refund.
        """
        self._authorize(account, "sale", "refund", "update")
        with self._uow_factory() as uow:
            refund = getattr(uow, "refunds").get(refund_id)
            if not refund:
                raise RefundNotFoundError()
                
            refund.mark_failed()
            getattr(uow, "refunds").update(refund)
            uow.commit()
            return ServiceResult(data=refund)
