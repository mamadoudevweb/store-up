"""Catalog domain exceptions.

All errors use a `CATALOG_` prefix to keep codes unique across domains.
They subclass the appropriate generic error from core for correct HTTP semantics.
"""
from __future__ import annotations

from src.core.services.errors import ConflictError, NotFoundError, ValidationError


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


class ProductVariantNotFound(NotFoundError):
    code = "CATALOG_PRODUCT_VARIANT_NOT_FOUND"
    message = "Product variant not found"


class LastVariantError(ValidationError):
    code = "CATALOG_LAST_VARIANT"
    message = "Cannot delete the last variant of a product — delete the product instead"


class ProductCategoryNotFound(NotFoundError):
    code = "CATALOG_PRODUCT_CATEGORY_NOT_FOUND"
    message = "Product is not assigned to that category"


class AttributeNotFound(NotFoundError):
    code = "CATALOG_ATTRIBUTE_NOT_FOUND"
    message = "Attribute not found"


class AttributeValueNotFound(NotFoundError):
    code = "CATALOG_ATTRIBUTE_VALUE_NOT_FOUND"
    message = "Attribute value not found"
