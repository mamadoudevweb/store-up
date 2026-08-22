"""StockMovement entity."""
from __future__ import annotations
from uuid import UUID

import uuid
from dataclasses import dataclass
from datetime import datetime

from src.core.entities.base_entity import BaseEntity


@dataclass(kw_only=True)
class StockMovement(BaseEntity[UUID]):
    id: uuid.UUID
    product_id: uuid.UUID
    quantity_change: int
    reason: str
    reference_id: str | None = None

    @classmethod
    def create(
        cls,
        product_id: uuid.UUID,
        quantity_change: int,
        reason: str,
        reference_id: str | None = None,
    ) -> StockMovement:
        from datetime import timezone
        return cls(
            id=uuid.uuid4(),
            product_id=product_id,
            quantity_change=quantity_change,
            reason=reason,
            reference_id=reference_id,
            created_at=datetime.now(timezone.utc),
        )
