"""Product service — manages the conceptual product (no pricing/SKU here)."""
from __future__ import annotations

import uuid
from typing import Callable

from src.core.repositories.base_uow import BaseUnitOfWork
from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.result import ServiceResult
from src.core.entities.pagination import Pagination
from src.domains.catalog.entities import Product, ProductStatus
from src.domains.catalog.exceptions import ProductNotFound
from src.domains.catalog.repositories.filters import ProductFilter, ProductVariantFilter


class ProductService(BaseService):
    def __init__(self, uow_factory: Callable[[], BaseUnitOfWork]) -> None:
        super().__init__(uow_factory)

    def create_product(
        self,
        actor: SupportsPermissionCheck,
        name: str,
        sku: str,
        cost_price: int,
        sell_price: int,
        description: str | None = None,
        brand_id: uuid.UUID | None = None,
    ) -> ServiceResult[Product]:
        """Create a Product and its mandatory first Variant atomically."""
        from src.domains.catalog.entities import ProductVariant
        self._authorize(actor, "catalog", "product", "create")
        with self._uow_factory() as uow:
            product = Product.create(name=name, description=description, brand_id=brand_id)
            product = uow.products.add(product)
            uow.track(product)

            assert product.id is not None
            # First variant is always created alongside the product
            if uow.product_variants.exists(ProductVariantFilter(sku=sku)):
                from src.domains.catalog.exceptions import DuplicateSkuError
                raise DuplicateSkuError(sku=sku)
            variant = ProductVariant.create(
                product_id=product.id,
                sku=sku,
                cost_price=cost_price,
                sell_price=sell_price,
            )
            uow.product_variants.add(variant)
            uow.track(variant)
        return ServiceResult(data=product)

    def get_product(
        self, actor: SupportsPermissionCheck, product_id: uuid.UUID
    ) -> ServiceResult[Product]:
        self._authorize(actor, "catalog", "product", "read")
        with self._uow_factory() as uow:
            product = uow.products.get(ProductFilter(id=product_id))
        if product is None:
            raise ProductNotFound()
        return ServiceResult(data=product)

    def list_products(
        self, actor: SupportsPermissionCheck, filters: ProductFilter
    ) -> ServiceResult[Pagination[Product]]:
        self._authorize(actor, "catalog", "product", "read")
        with self._uow_factory() as uow:
            page = uow.products.list(filters)
        return ServiceResult(data=page)

    def update_product(
        self,
        actor: SupportsPermissionCheck,
        product_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        brand_id: uuid.UUID | None = None,
    ) -> ServiceResult[Product]:
        self._authorize(actor, "catalog", "product", "update")
        with self._uow_factory() as uow:
            product = uow.products.get(ProductFilter(id=product_id))
            if product is None:
                raise ProductNotFound()
            product.update(name=name, description=description, brand_id=brand_id)
            product = uow.products.update(product)
            uow.track(product)
        return ServiceResult(data=product)

    def change_status(
        self,
        actor: SupportsPermissionCheck,
        product_id: uuid.UUID,
        new_status: ProductStatus,
    ) -> ServiceResult[Product]:
        self._authorize(actor, "catalog", "product", "update")
        with self._uow_factory() as uow:
            product = uow.products.get(ProductFilter(id=product_id))
            if product is None:
                raise ProductNotFound()
            product.change_status(new_status)
            product = uow.products.update(product)
            uow.track(product)
        return ServiceResult(data=product)

    def delete_product(
        self, actor: SupportsPermissionCheck, product_id: uuid.UUID
    ) -> ServiceResult[None]:
        """Soft-delete: archives the product (and all its variants via service)."""
        self._authorize(actor, "catalog", "product", "delete")
        with self._uow_factory() as uow:
            product = uow.products.get(ProductFilter(id=product_id))
            if product is None:
                raise ProductNotFound()
            product.mark_deleted()
            uow.products.update(product)
            uow.track(product)
            # Archive all variants
            variants = uow.product_variants.list(
                ProductVariantFilter(product_id=product_id)
            ).items
            for v in variants:
                v.mark_deleted()
                uow.product_variants.update(v)
                uow.track(v)
        return ServiceResult(data=None)
