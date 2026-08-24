"""ProductCategory service — manages many-to-many product↔category assignments."""
from __future__ import annotations

import uuid
from typing import Callable

from src.core.repositories.base_uow import BaseUnitOfWork
from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.result import ServiceResult
from src.core.entities.pagination import Pagination
from src.domains.catalog.entities import ProductCategory
from src.domains.catalog.exceptions import ProductCategoryNotFound, ProductNotFound
from src.domains.catalog.repositories.filters import ProductCategoryFilter, ProductFilter


class ProductCategoryService(BaseService):
    def __init__(self, uow_factory: Callable[[], BaseUnitOfWork]) -> None:
        super().__init__(uow_factory)

    def assign_category(
        self,
        actor: SupportsPermissionCheck,
        product_id: uuid.UUID,
        category_id: uuid.UUID,
    ) -> ServiceResult[ProductCategory]:
        self._authorize(actor, "catalog", "product_category", "create")
        with self._uow_factory() as uow:
            if uow.products.get(ProductFilter(id=product_id)) is None:
                raise ProductNotFound()
            pc = ProductCategory.assign(product_id=product_id, category_id=category_id)
            pc = uow.product_categories.add(pc)
            uow.track(pc)
        return ServiceResult(data=pc)

    def list_categories(
        self, actor: SupportsPermissionCheck, product_id: uuid.UUID
    ) -> ServiceResult[Pagination[ProductCategory]]:
        self._authorize(actor, "catalog", "product_category", "read")
        with self._uow_factory() as uow:
            page = uow.product_categories.list(ProductCategoryFilter(product_id=product_id))
        return ServiceResult(data=page)

    def unassign_category(
        self,
        actor: SupportsPermissionCheck,
        product_id: uuid.UUID,
        category_id: uuid.UUID,
    ) -> ServiceResult[None]:
        self._authorize(actor, "catalog", "product_category", "delete")
        with self._uow_factory() as uow:
            pc = uow.product_categories.get(
                ProductCategoryFilter(product_id=product_id, category_id=category_id)
            )
            if pc is None:
                raise ProductCategoryNotFound()
            pc.unassign()
            uow.product_categories.delete(pc)
            uow.track(pc)
        return ServiceResult(data=None)
