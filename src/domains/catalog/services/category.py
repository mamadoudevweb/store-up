"""Category service."""
from __future__ import annotations

import uuid
from typing import Callable

from src.core.repositories.base_uow import BaseUnitOfWork
from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.result import ServiceResult
from src.core.entities.pagination import Pagination
from src.domains.catalog.entities import Category
from src.domains.catalog.exceptions import CategoryNotFound
from src.domains.catalog.repositories.filters import CategoryFilter


class CategoryService(BaseService):
    def __init__(self, uow_factory: Callable[[], BaseUnitOfWork]) -> None:
        super().__init__(uow_factory)

    def create_category(
        self,
        actor: SupportsPermissionCheck,
        name: str,
        parent_id: uuid.UUID | None = None,
    ) -> ServiceResult[Category]:
        self._authorize(actor, "catalog", "category", "create")
        with self._uow_factory() as uow:
            if parent_id and not uow.categories.exists(CategoryFilter(id=parent_id)):
                raise CategoryNotFound(f"Parent category {parent_id} not found.")
            category = Category(
                id=uuid.uuid4(), name=name, parent_id=parent_id,
            )
            category = uow.categories.add(category)
        return ServiceResult(data=category)

    def get_category(
        self, actor: SupportsPermissionCheck, category_id: uuid.UUID
    ) -> ServiceResult[Category]:
        self._authorize(actor, "catalog", "category", "read")
        with self._uow_factory() as uow:
            category = uow.categories.get(CategoryFilter(id=category_id))
        if category is None:
            raise CategoryNotFound()
        return ServiceResult(data=category)

    def list_categories(
        self, actor: SupportsPermissionCheck, filters: CategoryFilter
    ) -> ServiceResult[Pagination[Category]]:
        self._authorize(actor, "catalog", "category", "read")
        with self._uow_factory() as uow:
            page = uow.categories.list(filters)
        return ServiceResult(data=page)

    def update_category(
        self,
        actor: SupportsPermissionCheck,
        category_id: uuid.UUID,
        name: str,
        parent_id: uuid.UUID | None = None,
    ) -> ServiceResult[Category]:
        self._authorize(actor, "catalog", "category", "update")
        with self._uow_factory() as uow:
            category = uow.categories.get(CategoryFilter(id=category_id))
            if category is None:
                raise CategoryNotFound()
            if parent_id and parent_id != category.parent_id:
                if not uow.categories.exists(CategoryFilter(id=parent_id)):
                    raise CategoryNotFound(f"Parent category {parent_id} not found.")
            category.name = name
            category.parent_id = parent_id
            category = uow.categories.update(category)
        return ServiceResult(data=category)

    def delete_category(
        self, actor: SupportsPermissionCheck, category_id: uuid.UUID
    ) -> ServiceResult[None]:
        self._authorize(actor, "catalog", "category", "delete")
        with self._uow_factory() as uow:
            category = uow.categories.get(CategoryFilter(id=category_id))
            if category is None:
                raise CategoryNotFound()
            uow.categories.delete(category)
        return ServiceResult(data=None)
