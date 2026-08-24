"""ProductImage entity — scoped to ProductVariant."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.core.entities.base_entity import BaseEntity


@dataclass(kw_only=True)
class ProductImage(BaseEntity[uuid.UUID]):
    """An image belonging to a specific ProductVariant.

    The image with the lowest `order` value is the primary/cover image.
    No separate is_primary flag — reordering IS the primary-setting mechanism.
    """

    variant_id: uuid.UUID
    file_path: str
    order: int = 0

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def add(cls, variant_id: uuid.UUID, file_path: str, order: int = 0) -> "ProductImage":
        img = cls(id=uuid.uuid4(), variant_id=variant_id, file_path=file_path, order=order)
        from src.domains.catalog.events import ProductImageAdded
        if img.id is None:
            raise ValueError("img ID cannot be None")
        img.register_event(ProductImageAdded(image_id=img.id, variant_id=img.variant_id))
        return img

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def reorder(self, new_order: int) -> None:
        if self.id is None:
            raise ValueError("self ID cannot be None")
        self.order = new_order
        from src.domains.catalog.events import ProductImageReordered
        self.register_event(ProductImageReordered(image_id=self.id, variant_id=self.variant_id, order=new_order))

    def remove(self) -> None:
        if self.id is None:
            raise ValueError("self ID cannot be None")
        from src.domains.catalog.events import ProductImageRemoved
        self.register_event(ProductImageRemoved(image_id=self.id, variant_id=self.variant_id))
