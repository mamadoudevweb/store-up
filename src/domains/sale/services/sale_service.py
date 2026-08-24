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
        Create a pending sale after reserving stock for all requested line items.
        
        Parameters:
        	seller_account_id (uuid.UUID): Account receiving credit for the sale.
        	payment_method_id (uuid.UUID): Payment method used for the sale.
        	lines_data (list[dict[str, typing.Any]]): Sale lines containing variant IDs, quantities, unit prices, and optional line discounts.
        	customer_name (str | None): Optional customer name associated with the sale.
        	discount (int): Overall sale discount.
        
        Returns:
        	ServiceResult[Sale]: The newly created pending sale.
        
        Raises:
        	InsufficientStockError: If the requested quantity is unavailable for any line.
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
        """
        Mark a sale as completed.
        
        Parameters:
        	sale_id (uuid.UUID): Identifier of the sale to complete.
        
        Returns:
        	ServiceResult[Sale]: The completed sale.
        
        Raises:
        	SaleNotFoundError: If the sale does not exist.
        """
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
        """
        Marks a sale as failed and releases its reserved stock.
        
        Parameters:
        	sale_id (uuid.UUID): Identifier of the sale to fail.
        	reason (str): Explanation for the sale failure.
        
        Raises:
        	SaleNotFoundError: If the sale does not exist.
        
        Returns:
        	ServiceResult[Sale]: The failed sale.
        """
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
        """
        Process a refund for a sale and update the refunded quantities of its sale lines.
        
        Parameters:
            account (SupportsPermissionCheck): Account requesting the refund.
            sale_id (uuid.UUID): Identifier of the sale to refund.
            refund_id (uuid.UUID): Identifier of the refund.
            lines_data (list[dict[str, typing.Any]]): Sale line identifiers and quantities to refund.
            amount (int): Refund amount.
        
        Returns:
            ServiceResult[Sale]: The updated sale.
        
        Raises:
            SaleNotFoundError: If the sale does not exist.
        """
        self._authorize(account, "sale", "sale", "update")
        with self._uow_factory() as uow:
            sale = getattr(uow, "sales").get(sale_id)
            if not sale:
                raise SaleNotFoundError()
                
            # Increment refunded_quantity for each line
            for line_data in lines_data:
                sale_line_id = line_data["sale_line_id"]
                quantity = line_data["quantity"]
                sale_line = next((sl for sl in sale.lines if str(sl.id) == str(sale_line_id)), None)
                if sale_line:
                    sale_line.refunded_quantity += quantity

            sale.process_refund(refund_id=refund_id, amount=amount)
            
            getattr(uow, "sales").update(sale)
            uow.track(sale)
            uow.commit()
            return ServiceResult(data=sale)
