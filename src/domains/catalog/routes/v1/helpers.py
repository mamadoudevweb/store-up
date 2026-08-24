"""Catalog route helpers — serializers and domain service accessor."""
from __future__ import annotations

from typing import Any
from flask import current_app

from src.domains.catalog.routes.v1.schemas.product_schemas import (
    AttributeResponse,
    AttributeValueResponse,
    BrandResponse,
    CategoryResponse,
    ProductCategoryResponse,
    ProductImageResponse,
    ProductResponse,
    ProductVariantResponse,
)


def _get_catalog() -> Any:
    """Return the CatalogDomainService from the current app context."""
    return current_app.extensions["domain_service"].catalog


def serialize_category(category: Any) -> dict[str, Any]:
    return CategoryResponse.model_validate(category).model_dump(mode="json")


def serialize_brand(brand: Any) -> dict[str, Any]:
    return BrandResponse.model_validate(brand).model_dump(mode="json")


def serialize_product(product: Any) -> dict[str, Any]:
    return ProductResponse.model_validate(product).model_dump(mode="json")


def serialize_variant(variant: Any) -> dict[str, Any]:
    return ProductVariantResponse.model_validate(variant).model_dump(mode="json")


def serialize_product_category(pc: Any) -> dict[str, Any]:
    return ProductCategoryResponse.model_validate(pc).model_dump(mode="json")


def serialize_product_image(image: Any) -> dict[str, Any]:
    return ProductImageResponse.model_validate(image).model_dump(mode="json")


def serialize_attribute(attr: Any) -> dict[str, Any]:
    return AttributeResponse.model_validate(attr).model_dump(mode="json")


def serialize_attribute_value(av: Any) -> dict[str, Any]:
    return AttributeValueResponse.model_validate(av).model_dump(mode="json")
