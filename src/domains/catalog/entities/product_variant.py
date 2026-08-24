"""ProductVariant entity — the actual sellable unit."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.core.entities.base_entity import BaseEntity
from src.domains.catalog.entities.enums import VariantStatus


@dataclass(kw_only=True)
class ProductVariant(BaseEntity[uuid.UUID]):
    """The actual sellable unit.

    Inventory, Sales, and Cart reference variant_id, never product_id.
    A Product always has at least one Variant (enforced at service layer).
    """

    product_id: uuid.UUID
    sku: str
    cost_price: int  # cents
    sell_price: int  # cents
    status: VariantStatus = VariantStatus.DRAFT

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def create(
        cls,
        product_id: uuid.UUID,
        sku: str,
        cost_price: int,
        sell_price: int,
    ) -> "ProductVariant":
        variant = cls(
            id=uuid.uuid4(),
            product_id=product_id,
            sku=sku,
            cost_price=cost_price,
            sell_price=sell_price,
            status=VariantStatus.DRAFT,
        )
        from src.domains.catalog.events import VariantCreated
        if variant.id is None:
            raise ValueError("variant ID cannot be None")
        variant.register_event(
            VariantCreated(variant_id=variant.id, product_id=variant.product_id, sku=variant.sku)
        )
        return variant

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def update(
        self,
        sku: str | None = None,
        cost_price: int | None = None,
        sell_price: int | None = None,
    ) -> None:
        if sku is not None:
            self.sku = sku
        if cost_price is not None:
            self.cost_price = cost_price
        if sell_price is not None:
            self.sell_price = sell_price
        from src.domains.catalog.events import VariantUpdated
        if self.id is None:
            raise ValueError("self ID cannot be None")
        self.register_event(VariantUpdated(variant_id=self.id, product_id=self.product_id, sku=self.sku))

    def change_status(self, new_status: VariantStatus) -> None:
        if self.id is None:
            raise ValueError("self ID cannot be None")
        old_status = self.status
        self.status = new_status
        from src.domains.catalog.events import VariantStatusChanged
        self.register_event(
            VariantStatusChanged(
                variant_id=self.id,
                old_status=old_status.value,
                new_status=new_status.value,
            )
        )

    def mark_deleted(self) -> None:
        if self.id is None:
            raise ValueError("self ID cannot be None")
        self.change_status(VariantStatus.ARCHIVED)
        from src.domains.catalog.events import VariantDeleted
        self.register_event(VariantDeleted(variant_id=self.id, product_id=self.product_id))
