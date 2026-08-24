"""Product entity."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.core.entities.base_entity import BaseEntity
from src.domains.catalog.entities.enums import ProductStatus


@dataclass(kw_only=True)
class Product(BaseEntity[uuid.UUID]):
    """A conceptual item — not directly sellable, not directly priced.

    Pricing, SKU, and images live on ProductVariant.
    A Product always has at least one Variant (enforced at service layer).
    """

    name: str
    description: str | None = None
    brand_id: uuid.UUID | None = None
    status: ProductStatus = ProductStatus.DRAFT

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def create(
        cls,
        name: str,
        description: str | None = None,
        brand_id: uuid.UUID | None = None,
    ) -> "Product":
        product = cls(
            id=uuid.uuid4(),
            name=name,
            description=description,
            brand_id=brand_id,
            status=ProductStatus.DRAFT,
        )
        from src.domains.catalog.events import ProductCreated
        if product.id is None:
            raise ValueError("product ID cannot be None")
        product.register_event(ProductCreated(product_id=product.id, name=product.name))
        return product

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def update(
        self,
        name: str | None = None,
        description: str | None = None,
        brand_id: uuid.UUID | None = None,
    ) -> None:
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if brand_id is not None:
            self.brand_id = brand_id
        from src.domains.catalog.events import ProductUpdated
        if self.id is None:
            raise ValueError("self ID cannot be None")
        self.register_event(ProductUpdated(product_id=self.id, name=self.name))

    def change_status(self, new_status: ProductStatus) -> None:
        if self.id is None:
            raise ValueError("self ID cannot be None")
        old_status = self.status
        self.status = new_status
        from src.domains.catalog.events import ProductStatusChanged
        self.register_event(
            ProductStatusChanged(
                product_id=self.id,
                old_status=old_status.value,
                new_status=new_status.value,
            )
        )

    def mark_deleted(self) -> None:
        if self.id is None:
            raise ValueError("self ID cannot be None")
        self.change_status(ProductStatus.ARCHIVED)
        from src.domains.catalog.events import ProductDeleted
        self.register_event(ProductDeleted(product_id=self.id))
