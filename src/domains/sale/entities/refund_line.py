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
        if quantity <= 0:
            raise ValueError("Refund line quantity must be positive")
        
        return cls(
            id=uuid.uuid4(),
            refund_id=refund_id,
            sale_line_id=sale_line_id,
            quantity=quantity,
        )
