"""Catalog domain enums."""
from __future__ import annotations

import enum


class ProductStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


# Variant uses the same three states, independently from the parent product
VariantStatus = ProductStatus
