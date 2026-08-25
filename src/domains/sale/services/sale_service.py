import uuid
import typing

from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.result import ServiceResult
from src.domains.sale.entities.sale import Sale
from src.domains.sale.entities.sale_line import SaleLine
from src.domains.sale.exceptions import InsufficientStockError, SaleNotFoundError


class SaleService(BaseService):
    def checkout(
        self,
        account: SupportsPermissionCheck,
        seller_account_id: uuid.UUID,
        payment_method_id: uuid.UUID,
        lines_data: list[dict[str, typing.Any]],
        customer_name: str | None = None,
        discount: int = 0,
    ) -> ServiceResult[Sale]:
        """
        Initiates a sale transaction.
        Reserves stock synchronously and creates a Sale in PENDING state.
        """
        self._authorize(account, "sale", "sale", "create")
        
        lines_data_sorted = sorted(lines_data, key=lambda x: str(x["variant_id"]))
        
        with self._uow_factory() as uow:
            for line_data in lines_data_sorted:
                variant_id = line_data["variant_id"]
                qty = line_data["quantity"]
                success = getattr(uow, "stock_items").atomic_reserve(variant_id, qty)
                if not success:
                    uow.rollback()
                    raise InsufficientStockError(f"Insufficient stock for variant {variant_id}")

            sale_id = uuid.uuid4()
            sale_lines = [
                SaleLine.create(
                    sale_id=sale_id,
                    variant_id=line_data["variant_id"],
                    quantity=line_data["quantity"],
                    unit_price=line_data["unit_price"],
                    discount=line_data.get("discount", 0),
                )
                for line_data in lines_data_sorted
            ]
            
            sale = Sale.checkout(
                seller_account_id=seller_account_id,
                payment_method_id=payment_method_id,
                lines=sale_lines,
                customer_name=customer_name,
                discount=discount,
            )
            sale.id = sale_id
            for line in sale.lines:
                line.sale_id = sale.id
                
            getattr(uow, "sales").add(sale)
            uow.track(sale)
            uow.commit()
            
            return ServiceResult(data=sale)

    def complete_sale(self, account: SupportsPermissionCheck, sale_id: uuid.UUID) -> ServiceResult[Sale]:
        """Called by event handler when payment is successful."""
        self._authorize(account, "sale", "sale", "update")
        with self._uow_factory() as uow:
            sale = getattr(uow, "sales").get(sale_id)
            if not sale:
                raise SaleNotFoundError()
                
            sale.mark_completed()
            getattr(uow, "sales").update(sale)
            uow.track(sale)
            uow.commit()
            return ServiceResult(data=sale)

    def fail_sale(self, account: SupportsPermissionCheck, sale_id: uuid.UUID, reason: str) -> ServiceResult[Sale]:
        """Called by event handler when payment fails. Releases stock."""
        self._authorize(account, "sale", "sale", "update")
        with self._uow_factory() as uow:
            sale = getattr(uow, "sales").get(sale_id)
            if not sale:
                raise SaleNotFoundError()
                
            sale.mark_failed(reason)
            
            for line in sale.lines:
                getattr(uow, "stock_items").atomic_release(line.variant_id, line.quantity)
                
            getattr(uow, "sales").update(sale)
            uow.track(sale)
            uow.commit()
            return ServiceResult(data=sale)

    def process_refund(self, account: SupportsPermissionCheck, sale_id: uuid.UUID, refund_id: uuid.UUID, lines_data: list[dict[str, typing.Any]], amount: int) -> ServiceResult[Sale]:
        """Called by event handler when a refund is requested. Mutates sale state and emits SaleReturned."""
        self._authorize(account, "sale", "sale", "update")
        with self._uow_factory() as uow:
            sale = getattr(uow, "sales").get(sale_id)
            if not sale:
                raise SaleNotFoundError()
                
            # Aggregate requested lines
            import uuid
            aggregated_requests: dict[uuid.UUID, int] = {}
            for line_data in lines_data:
                sale_line_id = uuid.UUID(str(line_data["sale_line_id"]))
                aggregated_requests[sale_line_id] = aggregated_requests.get(sale_line_id, 0) + line_data["quantity"]

            # Increment refunded_quantity for each line after revalidation
            for sale_line_id, quantity in aggregated_requests.items():
                sale_line = next((sl for sl in sale.lines if str(sl.id) == str(sale_line_id)), None)
                if sale_line:
                    if sale_line.refunded_quantity + quantity > sale_line.quantity:
                        from src.domains.sale.exceptions import RefundQuantityExceededError
                        raise RefundQuantityExceededError(f"Cannot refund more than sold for line {sale_line_id}")
                    sale_line.refunded_quantity += quantity

            sale.process_refund(refund_id=refund_id, amount=amount)
            
            getattr(uow, "sales").update(sale)
            uow.track(sale)
            uow.commit()
            return ServiceResult(data=sale)
