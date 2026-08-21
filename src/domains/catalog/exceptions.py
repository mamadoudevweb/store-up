"""Catalog domain exceptions.

All errors use a `CATALOG_` prefix to keep codes unique across domains.
They subclass the appropriate generic error from core for correct HTTP semantics.
"""
from __future__ import annotations

from src.core.services.errors import ConflictError, NotFoundError


class ProductNotFound(NotFoundError):
    code = "CATALOG_PRODUCT_NOT_FOUND"
    message = "Product not found"


class DuplicateSkuError(ConflictError):
    code = "CATALOG_DUPLICATE_SKU"
    message = "A product with this SKU already exists"


class BrandNotFound(NotFoundError):
    code = "CATALOG_BRAND_NOT_FOUND"
    message = "Brand not found"


class CategoryNotFound(NotFoundError):
    code = "CATALOG_CATEGORY_NOT_FOUND"
    message = "Category not found"


class ProductImageNotFound(NotFoundError):
    code = "CATALOG_PRODUCT_IMAGE_NOT_FOUND"
    message = "Product image not found"
