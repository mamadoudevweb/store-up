"""Attribute and AttributeValue entities — normalized attribute catalog."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.core.entities.base_entity import BaseEntity


@dataclass(kw_only=True)
class Attribute(BaseEntity[uuid.UUID]):
    """An attribute type, e.g. 'Color', 'Size'. Name must be unique."""

    name: str

    @classmethod
    def create(cls, name: str) -> "Attribute":
        attr = cls(id=uuid.uuid4(), name=name)
        from src.domains.catalog.events import AttributeCreated
        if attr.id is None:
            raise ValueError("attr ID cannot be None")
        attr.register_event(AttributeCreated(attribute_id=attr.id, name=attr.name))
        return attr


@dataclass(kw_only=True)
class AttributeValue(BaseEntity[uuid.UUID]):
    """A concrete value for an attribute, e.g. 'Red' for 'Color'. Unique per attribute."""

    attribute_id: uuid.UUID
    value: str

    @classmethod
    def create(cls, attribute_id: uuid.UUID, value: str) -> "AttributeValue":
        av = cls(id=uuid.uuid4(), attribute_id=attribute_id, value=value)
        from src.domains.catalog.events import AttributeValueCreated
        if av.id is None:
            raise ValueError("av ID cannot be None")
        av.register_event(
            AttributeValueCreated(attribute_value_id=av.id, attribute_id=av.attribute_id, value=av.value)
        )
        return av
