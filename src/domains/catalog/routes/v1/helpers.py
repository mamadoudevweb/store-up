"""Catalog route helpers — serializers and domain service accessor."""
from __future__ import annotations

from flask import current_app

from src.domains.catalog.routes.v1.schemas.product_schemas import (
    BrandResponse,
    CategoryResponse,
    ProductImageResponse,
    ProductResponse,
)


def _get_catalog():  # type: ignore[no-untyped-def]
    """Return the CatalogDomainService from the current app context."""
    return current_app.extensions["domain_service"].catalog


def serialize_category(category) -> dict:  # type: ignore[no-untyped-def]
    return CategoryResponse.model_validate(category).model_dump(mode="json")


def serialize_brand(brand) -> dict:  # type: ignore[no-untyped-def]
    return BrandResponse.model_validate(brand).model_dump(mode="json")


def serialize_product(product) -> dict:  # type: ignore[no-untyped-def]
    return ProductResponse.model_validate(product).model_dump(mode="json")


def serialize_product_image(image) -> dict:  # type: ignore[no-untyped-def]
    return ProductImageResponse.model_validate(image).model_dump(mode="json")
