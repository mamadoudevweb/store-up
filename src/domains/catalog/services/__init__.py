"""Catalog domain service — aggregates all entity services in this domain."""
from __future__ import annotations

from typing import Callable

from src.core.repositories.base_uow import BaseUnitOfWork

from .attribute import AttributeService
from .brand import BrandService
from .category import CategoryService
from .product import ProductService
from .product_category import ProductCategoryService
from .product_image import ProductImageService
from .product_variant import ProductVariantService


class CatalogDomainService:
    """Aggregates every entity service in the catalog domain.

    Routes reach them via: ``domain_service().catalog.product.create_product(...)``
    """

    from src.core.services.storage import FileStorageService

    def __init__(self, uow_factory: Callable[[], BaseUnitOfWork], storage: FileStorageService) -> None:
        self.product = ProductService(uow_factory)
        self.variant = ProductVariantService(uow_factory)
        self.product_category = ProductCategoryService(uow_factory)
        self.brand = BrandService(uow_factory, storage)
        self.category = CategoryService(uow_factory)
        self.product_image = ProductImageService(uow_factory, storage)
        self.attribute = AttributeService(uow_factory)
