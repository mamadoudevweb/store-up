from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.core.entities.base_entity import BaseEntity


@dataclass(kw_only=True)
class RefundLine(BaseEntity[uuid.UUID]):
    id: uuid.UUID
    refund_id: uuid.UUID
    sale_line_id: uuid.UUID
    quantity: int

    @classmethod
    def create(
        cls,
        refund_id: uuid.UUID,
        sale_line_id: uuid.UUID,
        quantity: int,
    ) -> RefundLine:
        """
        Create a refund line for a sale line.
        
        Parameters:
        	refund_id (uuid.UUID): Identifier of the refund.
        	sale_line_id (uuid.UUID): Identifier of the sale line being refunded.
        	quantity (int): Number of units to refund.
        
        Returns:
        	RefundLine: A refund line with a generated identifier.
        
        Raises:
        	ValueError: If quantity is less than or equal to zero.
        """
        if quantity <= 0:
            raise ValueError("Refund line quantity must be positive")
        
        return cls(
            id=uuid.uuid4(),
            refund_id=refund_id,
            sale_line_id=sale_line_id,
            quantity=quantity,
        )
