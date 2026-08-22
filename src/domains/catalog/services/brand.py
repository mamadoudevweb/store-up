"""Brand service."""
from __future__ import annotations

import os
import uuid
from typing import BinaryIO, Callable

from src.core.repositories.base_uow import BaseUnitOfWork
from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.result import ServiceResult
from src.core.entities.pagination import Pagination
from src.domains.catalog.entities import Brand
from src.domains.catalog.exceptions import BrandNotFound
from src.domains.catalog.repositories.filters import BrandFilter


class BrandService(BaseService):
    def __init__(self, uow_factory: Callable[[], BaseUnitOfWork], upload_folder: str) -> None:
        super().__init__(uow_factory)
        self._upload_folder = upload_folder

    def create_brand(
        self,
        actor: SupportsPermissionCheck,
        name: str,
        description: str | None = None,
    ) -> ServiceResult[Brand]:
        self._authorize(actor, "catalog", "brand", "create")
        with self._uow_factory() as uow:
            brand = Brand(id=uuid.uuid4(), name=name, description=description)
            brand = uow.brands.add(brand)
        return ServiceResult(data=brand)

    def get_brand(
        self, actor: SupportsPermissionCheck, brand_id: uuid.UUID
    ) -> ServiceResult[Brand]:
        self._authorize(actor, "catalog", "brand", "read")
        with self._uow_factory() as uow:
            brand = uow.brands.get(BrandFilter(id=brand_id, is_active=True))
        if brand is None:
            raise BrandNotFound()
        return ServiceResult(data=brand)

    def list_brands(
        self, actor: SupportsPermissionCheck, filters: BrandFilter
    ) -> ServiceResult[Pagination[Brand]]:
        self._authorize(actor, "catalog", "brand", "read")
        with self._uow_factory() as uow:
            page = uow.brands.list(filters)
        return ServiceResult(data=page)

    def update_brand(
        self,
        actor: SupportsPermissionCheck,
        brand_id: uuid.UUID,
        name: str,
        description: str | None = None,
    ) -> ServiceResult[Brand]:
        self._authorize(actor, "catalog", "brand", "update")
        with self._uow_factory() as uow:
            brand = uow.brands.get(BrandFilter(id=brand_id, is_active=True))
            if brand is None:
                raise BrandNotFound()
            brand.name = name
            brand.description = description
            brand = uow.brands.update(brand)
        return ServiceResult(data=brand)

    def delete_brand(
        self, actor: SupportsPermissionCheck, brand_id: uuid.UUID
    ) -> ServiceResult[None]:
        self._authorize(actor, "catalog", "brand", "delete")
        with self._uow_factory() as uow:
            brand = uow.brands.get(BrandFilter(id=brand_id, is_active=True))
            if brand is None:
                raise BrandNotFound()
            brand.is_active = False
            uow.brands.update(brand)
        return ServiceResult(data=None)

    def upload_logo(
        self,
        actor: SupportsPermissionCheck,
        brand_id: uuid.UUID,
        filename: str,
        file_stream: BinaryIO,
    ) -> ServiceResult[Brand]:
        self._authorize(actor, "catalog", "brand", "update")
        with self._uow_factory() as uow:
            brand = uow.brands.get(BrandFilter(id=brand_id, is_active=True))
            if brand is None:
                raise BrandNotFound()

            os.makedirs(self._upload_folder, exist_ok=True)
            ext = os.path.splitext(filename)[1]
            safe_filename = f"{uuid.uuid4().hex}{ext}"
            file_path = os.path.join(self._upload_folder, safe_filename)

            with open(file_path, "wb") as f:
                f.write(file_stream.read())

            if brand.logo_path and os.path.exists(
                os.path.join(self._upload_folder, brand.logo_path)
            ):
                try:
                    os.remove(os.path.join(self._upload_folder, brand.logo_path))
                except OSError:
                    pass

            brand.logo_path = safe_filename
            brand = uow.brands.update(brand)
        return ServiceResult(data=brand)

    def delete_logo(
        self, actor: SupportsPermissionCheck, brand_id: uuid.UUID
    ) -> ServiceResult[Brand]:
        self._authorize(actor, "catalog", "brand", "update")
        with self._uow_factory() as uow:
            brand = uow.brands.get(BrandFilter(id=brand_id, is_active=True))
            if brand is None:
                raise BrandNotFound()

            if brand.logo_path:
                full_path = os.path.join(self._upload_folder, brand.logo_path)
                if os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                    except OSError:
                        pass
                brand.logo_path = None
                brand = uow.brands.update(brand)
        return ServiceResult(data=brand)
