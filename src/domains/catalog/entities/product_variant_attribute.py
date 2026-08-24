"""ProductVariantAttribute — join between a Variant and its defining AttributeValues."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.core.entities.base_entity import BaseEntity


@dataclass(kw_only=True)
class ProductVariantAttribute(BaseEntity[uuid.UUID]):
    """Links a variant to a specific attribute value.

    Composite PK on (variant_id, attribute_id) — a variant can't have two
    values for the same attribute (enforced at DB level via composite PK).
    """

    variant_id: uuid.UUID
    attribute_id: uuid.UUID
    attribute_value_id: uuid.UUID

    @classmethod
    def set_attribute(
        cls,
        variant_id: uuid.UUID,
        attribute_id: uuid.UUID,
        attribute_value_id: uuid.UUID,
    ) -> "ProductVariantAttribute":
        pva = cls(
            id=uuid.uuid4(),
            variant_id=variant_id,
            attribute_id=attribute_id,
            attribute_value_id=attribute_value_id,
        )
        from src.domains.catalog.events import VariantAttributeSet
        assert pva.id is not None
        pva.register_event(
            VariantAttributeSet(
                variant_id=pva.variant_id,
                attribute_id=pva.attribute_id,
                attribute_value_id=pva.attribute_value_id,
            )
        )
        return pva
