"""ProductCategory entity — many-to-many join between Product and Category."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.core.entities.base_entity import BaseEntity


@dataclass(kw_only=True)
class ProductCategory(BaseEntity[uuid.UUID]):
    product_id: uuid.UUID
    category_id: uuid.UUID

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def assign(cls, product_id: uuid.UUID, category_id: uuid.UUID) -> "ProductCategory":
        pc = cls(id=uuid.uuid4(), product_id=product_id, category_id=category_id)
        from src.domains.catalog.events import ProductCategoryAssigned
        assert pc.id is not None
        pc.register_event(
            ProductCategoryAssigned(product_id=pc.product_id, category_id=pc.category_id)
        )
        return pc

    def unassign(self) -> None:
        from src.domains.catalog.events import ProductCategoryUnassigned
        self.register_event(
            ProductCategoryUnassigned(product_id=self.product_id, category_id=self.category_id)
        )
