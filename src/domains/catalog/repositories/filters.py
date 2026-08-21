"""Catalog domain filters."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.core.entities.pagination import EntityFilter


@dataclass(kw_only=True)
class CategoryFilter(EntityFilter):
    id: uuid.UUID | None = None
    name: str | None = None
    parent_id: uuid.UUID | None = None


@dataclass(kw_only=True)
class BrandFilter(EntityFilter):
    id: uuid.UUID | None = None
    name: str | None = None
    is_active: bool | None = None


@dataclass(kw_only=True)
class ProductFilter(EntityFilter):
    id: uuid.UUID | None = None
    sku: str | None = None
    name: str | None = None
    category_id: uuid.UUID | None = None
    brand_id: uuid.UUID | None = None
    is_active: bool | None = None


@dataclass(kw_only=True)
class ProductImageFilter(EntityFilter):
    id: uuid.UUID | None = None
    product_id: uuid.UUID | None = None
    is_primary: bool | None = None
