from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from src.core.entities.base_entity import BaseEntity
from src.domains.sale.entities.enums import SaleStatus
from src.domains.sale.entities.sale_line import SaleLine
from src.domains.sale.events import SaleCreated, SaleFailed, SaleReturned
from src.domains.sale.exceptions import InvalidSaleStateError


@dataclass(kw_only=True)
class Sale(BaseEntity[uuid.UUID]):
    id: uuid.UUID
    number: str | None
    customer_name: str | None
    seller_account_id: uuid.UUID
    status: SaleStatus
    payment_method_id: uuid.UUID
    discount: int
    subtotal: int
    total: int
    created_at: datetime
    returned_at: datetime | None = None
    failed_at: datetime | None = None
    
    lines: list[SaleLine] = field(default_factory=list)

    @classmethod
    def checkout(
        cls,
        seller_account_id: uuid.UUID,
        payment_method_id: uuid.UUID,
        lines: list[SaleLine],
        customer_name: str | None = None,
        discount: int = 0,
        number: str | None = None,
    ) -> Sale:
        from datetime import timezone
        
        if not lines:
            raise ValueError("Sale must have at least one line")
            
        subtotal = sum(line.subtotal for line in lines)
        if discount < 0:
            raise ValueError("Order-level discount cannot be negative")
            
        total = subtotal - discount
        
        if total < 0:
            raise ValueError("Total cannot be negative")
            
        if number is None:
            now = datetime.now(timezone.utc)
            number = f"SALE-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        sale = cls(
            id=uuid.uuid4(),
            number=number,
            customer_name=customer_name,
            seller_account_id=seller_account_id,
            status=SaleStatus.PENDING,
            payment_method_id=payment_method_id,
            discount=discount,
            subtotal=subtotal,
            total=total,
            created_at=datetime.now(timezone.utc),
            lines=lines, # :TODO: Enforce that a sale lines exists before creating any sale
        )
        
        # Ensure all lines have the correct sale_id
        for line in sale.lines:
            line.sale_id = sale.id

        sale.register_event(
            SaleCreated(
                sale_id=sale.id,
                seller_account_id=sale.seller_account_id,
                total=sale.total,
                payment_method_id=sale.payment_method_id,
            )
        )

        return sale

    def mark_completed(self) -> None:
        if self.status != SaleStatus.PENDING:
            raise InvalidSaleStateError("Only pending sales can be completed")
        
        self.status = SaleStatus.COMPLETED
        from src.domains.sale.events import SaleCompleted
        self.register_event(SaleCompleted(sale_id=self.id))

    def mark_failed(self, reason: str) -> None:
        if self.status != SaleStatus.PENDING:
            raise InvalidSaleStateError("Only pending sales can be failed")
            
        from datetime import datetime, timezone
        
        self.status = SaleStatus.FAILED
        self.failed_at = datetime.now(timezone.utc)
        self.register_event(SaleFailed(sale_id=self.id))

    def process_refund(self, refund_id: uuid.UUID, amount: int, refund_lines: list[dict[str, typing.Any]]) -> None:
        if self.status not in (SaleStatus.COMPLETED, SaleStatus.RETURNED):
            raise InvalidSaleStateError("Sale must be completed to process a refund")
            
        from datetime import datetime, timezone
        from src.domains.sale.events import RefundCompleted, SaleReturned
        
        self.register_event(
            RefundCompleted(
                refund_id=refund_id,
                sale_id=self.id,
                lines=refund_lines,
            )
        )
        
        all_refunded = all(line.refunded_quantity == line.quantity for line in self.lines)
        if all_refunded and self.status != SaleStatus.RETURNED:
            self.status = SaleStatus.RETURNED
            self.returned_at = datetime.now(timezone.utc)
            self.register_event(
                SaleReturned(
                    refund_id=refund_id,
                    sale_id=self.id,
                    amount=amount,
                )
            )

