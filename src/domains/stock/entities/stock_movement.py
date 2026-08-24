"""StockMovement entity."""
from __future__ import annotations
from uuid import UUID

import uuid
from dataclasses import dataclass
from datetime import datetime

from src.core.entities.base_entity import BaseEntity
from src.domains.stock.entities.enums import StockMovementReason, ReferenceType


@dataclass(kw_only=True)
class StockMovement(BaseEntity[UUID]):
    id: uuid.UUID
    stock_item_id: uuid.UUID
    quantity_change: int
    reason: StockMovementReason
    reference_type: ReferenceType
    reference_id: str | None = None

    @classmethod
    def create(
        cls,
        stock_item_id: uuid.UUID,
        quantity_change: int,
        reason: StockMovementReason,
        reference_type: ReferenceType,
        reference_id: str | None = None,
    ) -> StockMovement:
        from datetime import timezone
        return cls(
            id=uuid.uuid4(),
            stock_item_id=stock_item_id,
            quantity_change=quantity_change,
            reason=reason,
            reference_type=reference_type,
            reference_id=reference_id,
            created_at=datetime.now(timezone.utc),
        )
