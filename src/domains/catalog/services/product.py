"""Product service."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Callable

from src.core.repositories.base_uow import BaseUnitOfWork
from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.result import ServiceResult
from src.core.entities.pagination import Pagination
from src.domains.catalog.entities import Product
from src.domains.catalog.exceptions import DuplicateSkuError, ProductNotFound
from src.domains.catalog.repositories.filters import ProductFilter


class ProductService(BaseService):
    def __init__(self, uow_factory: Callable[[], BaseUnitOfWork]) -> None:
        super().__init__(uow_factory)

    def create_product(
        self,
        actor: SupportsPermissionCheck,
        sku: str,
        name: str,
        cost_price: int,
        sell_price: int,
        description: str | None = None,
        category_id: uuid.UUID | None = None,
        brand_id: uuid.UUID | None = None,
    ) -> ServiceResult[Product]:
        self._authorize(actor, "catalog", "product", "create")
        with self._uow_factory() as uow:
            if uow.products.exists(ProductFilter(sku=sku)):
                raise DuplicateSkuError(sku=sku)
            product = Product(
                id=uuid.uuid4(),
                sku=sku,
                name=name,
                cost_price=cost_price,
                sell_price=sell_price,
                description=description,
                category_id=category_id,
                brand_id=brand_id,
            )
            product = uow.products.add(product)
            uow.track(product)
        return ServiceResult(data=product)

    def get_product(
        self, actor: SupportsPermissionCheck, product_id: uuid.UUID
    ) -> ServiceResult[Product]:
        self._authorize(actor, "catalog", "product", "read")
        with self._uow_factory() as uow:
            product = uow.products.get(ProductFilter(id=product_id, is_active=True))
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
        sku: str,
        name: str,
        cost_price: int,
        sell_price: int,
        description: str | None = None,
        category_id: uuid.UUID | None = None,
        brand_id: uuid.UUID | None = None,
        is_active: bool = True,
    ) -> ServiceResult[Product]:
        self._authorize(actor, "catalog", "product", "update")
        with self._uow_factory() as uow:
            product = uow.products.get(ProductFilter(id=product_id, is_active=True))
            if product is None:
                raise ProductNotFound()
            product.sku = sku
            product.name = name
            product.cost_price = cost_price
            product.sell_price = sell_price
            product.description = description
            product.category_id = category_id
            product.brand_id = brand_id
            product.is_active = is_active
            product = uow.products.update(product)
        return ServiceResult(data=product)

    def delete_product(
        self, actor: SupportsPermissionCheck, product_id: uuid.UUID
    ) -> ServiceResult[None]:
        self._authorize(actor, "catalog", "product", "delete")
        with self._uow_factory() as uow:
            product = uow.products.get(ProductFilter(id=product_id, is_active=True))
            if product is None:
                raise ProductNotFound()
            product.is_active = False
            uow.products.update(product)
        return ServiceResult(data=None)
