from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from src.core.entities.base_entity import BaseEntity
from src.domains.sale.entities.enums import RefundStatus
from src.domains.sale.entities.refund_line import RefundLine


@dataclass(kw_only=True)
class Refund(BaseEntity[uuid.UUID]):
    id: uuid.UUID
    sale_id: uuid.UUID
    processed_by: uuid.UUID
    reason: str
    status: RefundStatus
    created_at: datetime
    
    lines: list[RefundLine] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        sale_id: uuid.UUID,
        processed_by: uuid.UUID,
        reason: str,
        lines: list[RefundLine],
    ) -> Refund:
        from datetime import timezone
        
        if not lines:
            raise ValueError("Refund must have at least one line")
            
        refund = cls(
            id=uuid.uuid4(),
            sale_id=sale_id,
            processed_by=processed_by,
            reason=reason,
            status=RefundStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            lines=lines, # :TODO: Enforce that a refund lines exists before ceating any refund
        )
        
        # Ensure all lines have the correct refund_id
        for line in refund.lines:
            line.refund_id = refund.id

        return refund

    def mark_processed(self) -> None:
        if self.status != RefundStatus.PENDING:
            raise ValueError(f"Cannot process refund in {self.status.value} state")
        self.status = RefundStatus.PROCESSED

    def mark_failed(self) -> None:
        if self.status != RefundStatus.PENDING:
            raise ValueError(f"Cannot fail refund in {self.status.value} state")
        self.status = RefundStatus.FAILED
