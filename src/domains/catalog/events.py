"""Events for the Catalog domain."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.core.entities.events import DomainEvent


# ── Product ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ProductCreated(DomainEvent):
    """Emitted when a new product is created."""
    product_id: uuid.UUID
    name: str


@dataclass(frozen=True)
class ProductUpdated(DomainEvent):
    product_id: uuid.UUID
    name: str


@dataclass(frozen=True)
class ProductStatusChanged(DomainEvent):
    product_id: uuid.UUID
    old_status: str
    new_status: str


@dataclass(frozen=True)
class ProductDeleted(DomainEvent):
    product_id: uuid.UUID


# ── ProductVariant ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class VariantCreated(DomainEvent):
    variant_id: uuid.UUID
    product_id: uuid.UUID
    sku: str


@dataclass(frozen=True)
class VariantUpdated(DomainEvent):
    variant_id: uuid.UUID
    product_id: uuid.UUID
    sku: str


@dataclass(frozen=True)
class VariantStatusChanged(DomainEvent):
    variant_id: uuid.UUID
    old_status: str
    new_status: str


@dataclass(frozen=True)
class VariantDeleted(DomainEvent):
    variant_id: uuid.UUID
    product_id: uuid.UUID


# ── ProductCategory ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ProductCategoryAssigned(DomainEvent):
    product_id: uuid.UUID
    category_id: uuid.UUID


@dataclass(frozen=True)
class ProductCategoryUnassigned(DomainEvent):
    product_id: uuid.UUID
    category_id: uuid.UUID


# ── Attribute / AttributeValue ────────────────────────────────────────────────

@dataclass(frozen=True)
class AttributeCreated(DomainEvent):
    attribute_id: uuid.UUID
    name: str


@dataclass(frozen=True)
class AttributeValueCreated(DomainEvent):
    attribute_value_id: uuid.UUID
    attribute_id: uuid.UUID
    value: str


# ── ProductVariantAttribute ───────────────────────────────────────────────────

@dataclass(frozen=True)
class VariantAttributeSet(DomainEvent):
    variant_id: uuid.UUID
    attribute_id: uuid.UUID
    attribute_value_id: uuid.UUID


# ── ProductImage ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ProductImageAdded(DomainEvent):
    image_id: uuid.UUID
    variant_id: uuid.UUID


@dataclass(frozen=True)
class ProductImageRemoved(DomainEvent):
    image_id: uuid.UUID
    variant_id: uuid.UUID


@dataclass(frozen=True)
class ProductImageReordered(DomainEvent):
    image_id: uuid.UUID
    variant_id: uuid.UUID
    order: int
