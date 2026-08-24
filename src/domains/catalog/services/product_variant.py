"""ProductVariant service."""
from __future__ import annotations

import uuid
from typing import Callable

from src.core.repositories.base_uow import BaseUnitOfWork
from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.result import ServiceResult
from src.core.entities.pagination import Pagination
from src.domains.catalog.entities import ProductVariant, VariantStatus
from src.domains.catalog.exceptions import ProductNotFound, ProductVariantNotFound
from src.domains.catalog.repositories.filters import ProductFilter, ProductVariantFilter


class ProductVariantService(BaseService):
    def __init__(self, uow_factory: Callable[[], BaseUnitOfWork]) -> None:
        super().__init__(uow_factory)

    def create_variant(
        self,
        actor: SupportsPermissionCheck,
        product_id: uuid.UUID,
        sku: str,
        cost_price: int,
        sell_price: int,
    ) -> ServiceResult[ProductVariant]:
        self._authorize(actor, "catalog", "product_variant", "create")
        with self._uow_factory() as uow:
            if uow.products.get(ProductFilter(id=product_id)) is None:
                raise ProductNotFound()
            if uow.product_variants.exists(ProductVariantFilter(sku=sku)):
                from src.domains.catalog.exceptions import DuplicateSkuError
                raise DuplicateSkuError(sku=sku)
            variant = ProductVariant.create(
                product_id=product_id, sku=sku, cost_price=cost_price, sell_price=sell_price
            )
            variant = uow.product_variants.add(variant)
            uow.track(variant)
        return ServiceResult(data=variant)

    def get_variant(
        self, actor: SupportsPermissionCheck, variant_id: uuid.UUID
    ) -> ServiceResult[ProductVariant]:
        self._authorize(actor, "catalog", "product_variant", "read")
        with self._uow_factory() as uow:
            variant = uow.product_variants.get(ProductVariantFilter(id=variant_id))
        if variant is None:
            raise ProductVariantNotFound()
        return ServiceResult(data=variant)

    def list_variants(
        self, actor: SupportsPermissionCheck, filters: ProductVariantFilter
    ) -> ServiceResult[Pagination[ProductVariant]]:
        self._authorize(actor, "catalog", "product_variant", "read")
        with self._uow_factory() as uow:
            page = uow.product_variants.list(filters)
        return ServiceResult(data=page)

    def update_variant(
        self,
        actor: SupportsPermissionCheck,
        variant_id: uuid.UUID,
        sku: str | None = None,
        cost_price: int | None = None,
        sell_price: int | None = None,
    ) -> ServiceResult[ProductVariant]:
        self._authorize(actor, "catalog", "product_variant", "update")
        with self._uow_factory() as uow:
            variant = uow.product_variants.get(ProductVariantFilter(id=variant_id))
            if variant is None:
                raise ProductVariantNotFound()
            variant.update(sku=sku, cost_price=cost_price, sell_price=sell_price)
            variant = uow.product_variants.update(variant)
            uow.track(variant)
        return ServiceResult(data=variant)

    def change_status(
        self,
        actor: SupportsPermissionCheck,
        variant_id: uuid.UUID,
        new_status: VariantStatus,
    ) -> ServiceResult[ProductVariant]:
        self._authorize(actor, "catalog", "product_variant", "update")
        with self._uow_factory() as uow:
            variant = uow.product_variants.get(ProductVariantFilter(id=variant_id))
            if variant is None:
                raise ProductVariantNotFound()
            variant.change_status(new_status)
            variant = uow.product_variants.update(variant)
            uow.track(variant)
        return ServiceResult(data=variant)

    def delete_variant(
        self, actor: SupportsPermissionCheck, variant_id: uuid.UUID
    ) -> ServiceResult[None]:
        """Archives the variant. Refuses if it is the last variant for its product."""
        self._authorize(actor, "catalog", "product_variant", "delete")
        with self._uow_factory() as uow:
            variant = uow.product_variants.get(ProductVariantFilter(id=variant_id))
            if variant is None:
                raise ProductVariantNotFound()
            siblings = uow.product_variants.list(
                ProductVariantFilter(product_id=variant.product_id)
            ).items
            if len(siblings) <= 1:
                from src.domains.catalog.exceptions import LastVariantError
                raise LastVariantError()
            variant.mark_deleted()
            uow.product_variants.update(variant)
            uow.track(variant)
        return ServiceResult(data=None)
