"""ProductImage service."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import BinaryIO, Callable

from src.core.repositories.base_uow import BaseUnitOfWork
from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.result import ServiceResult
from src.core.entities.pagination import Pagination
from src.domains.catalog.entities import ProductImage
from src.domains.catalog.exceptions import ProductImageNotFound, ProductNotFound
from src.domains.catalog.repositories.filters import ProductFilter, ProductImageFilter


class ProductImageService(BaseService):
    def __init__(self, uow_factory: Callable[[], BaseUnitOfWork], upload_folder: str) -> None:
        super().__init__(uow_factory)
        self._upload_folder = upload_folder

    def _save_file(self, filename: str, file_stream: BinaryIO) -> str:
        """Save a file to the upload folder and return the generated safe filename."""
        os.makedirs(self._upload_folder, exist_ok=True)
        ext = os.path.splitext(filename)[1]
        safe_filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(self._upload_folder, safe_filename)

        with open(file_path, "wb") as f:
            f.write(file_stream.read())
        return safe_filename

    def _delete_file(self, filename: str) -> None:
        """Delete a file from the upload folder if it exists."""
        full_path = os.path.join(self._upload_folder, filename)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except OSError:
                pass

    def upload_image(
        self,
        actor: SupportsPermissionCheck,
        product_id: uuid.UUID,
        filename: str,
        file_stream: BinaryIO,
        is_primary: bool = False,
        sort_order: int = 0,
    ) -> ServiceResult[ProductImage]:
        self._authorize(actor, "catalog", "product_image", "create")
        with self._uow_factory() as uow:
            if uow.products.get(ProductFilter(id=product_id)) is None:
                raise ProductNotFound()

            safe_filename = self._save_file(filename, file_stream)

            if is_primary:
                existing = uow.product_images.list(
                    ProductImageFilter(product_id=product_id)
                ).items
                for img in existing:
                    if img.is_primary:
                        img.is_primary = False
                        uow.product_images.update(img)

            image = ProductImage(
                id=uuid.uuid4(),
                product_id=product_id,
                file_path=safe_filename,
                is_primary=is_primary,
                sort_order=sort_order,
                created_at=datetime.now(timezone.utc),
            )
            image = uow.product_images.add(image)
        return ServiceResult(data=image)

    def list_images(
        self, actor: SupportsPermissionCheck, product_id: uuid.UUID
    ) -> ServiceResult[Pagination[ProductImage]]:
        self._authorize(actor, "catalog", "product_image", "read")
        with self._uow_factory() as uow:
            page = uow.product_images.list(ProductImageFilter(product_id=product_id))
        return ServiceResult(data=page)

    def set_primary(
        self,
        actor: SupportsPermissionCheck,
        product_id: uuid.UUID,
        image_id: uuid.UUID,
    ) -> ServiceResult[ProductImage]:
        self._authorize(actor, "catalog", "product_image", "update")
        with self._uow_factory() as uow:
            image = uow.product_images.get(
                ProductImageFilter(id=image_id, product_id=product_id)
            )
            if image is None:
                raise ProductImageNotFound()
            existing = uow.product_images.list(
                ProductImageFilter(product_id=product_id)
            ).items
            for img in existing:
                if img.is_primary:
                    img.is_primary = False
                    uow.product_images.update(img)
            image.is_primary = True
            image = uow.product_images.update(image)
        return ServiceResult(data=image)

    def delete_image(
        self,
        actor: SupportsPermissionCheck,
        product_id: uuid.UUID,
        image_id: uuid.UUID,
    ) -> ServiceResult[None]:
        self._authorize(actor, "catalog", "product_image", "delete")
        with self._uow_factory() as uow:
            image = uow.product_images.get(
                ProductImageFilter(id=image_id, product_id=product_id)
            )
            if image is None:
                raise ProductImageNotFound()
            self._delete_file(image.file_path)
            uow.product_images.delete(image)
        return ServiceResult(data=None)
