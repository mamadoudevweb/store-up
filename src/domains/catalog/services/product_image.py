"""ProductImage service — images now belong to ProductVariant."""
from __future__ import annotations

import uuid
from typing import BinaryIO, Callable

from src.core.repositories.base_uow import BaseUnitOfWork
from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.result import ServiceResult
from src.core.services.storage import FileStorageService
from src.core.entities.pagination import Pagination
from src.domains.catalog.entities import ProductImage
from src.domains.catalog.exceptions import ProductImageNotFound, ProductVariantNotFound
from src.domains.catalog.repositories.filters import ProductImageFilter, ProductVariantFilter


class ProductImageService(BaseService):

    def __init__(self, uow_factory: Callable[[], BaseUnitOfWork], storage: FileStorageService) -> None:
        super().__init__(uow_factory)
        self.storage = storage

    def upload_image(
        self,
        actor: SupportsPermissionCheck,
        variant_id: uuid.UUID,
        filename: str,
        file_stream: BinaryIO,
        order: int = 0,
    ) -> ServiceResult[ProductImage]:
        self._authorize(actor, "catalog", "product_image", "create")
        with self._uow_factory() as uow:
            if uow.product_variants.get(ProductVariantFilter(id=variant_id)) is None:
                raise ProductVariantNotFound()
            safe_filename = self.storage.save(filename, file_stream)
            image = ProductImage.add(variant_id=variant_id, file_path=safe_filename, order=order)
            image = uow.product_images.add(image)
            uow.track(image)
        return ServiceResult(data=image)

    def list_images(
        self, actor: SupportsPermissionCheck, variant_id: uuid.UUID
    ) -> ServiceResult[Pagination[ProductImage]]:
        self._authorize(actor, "catalog", "product_image", "read")
        with self._uow_factory() as uow:
            page = uow.product_images.list(ProductImageFilter(variant_id=variant_id))
        return ServiceResult(data=page)

    def set_primary(
        self,
        actor: SupportsPermissionCheck,
        variant_id: uuid.UUID,
        image_id: uuid.UUID,
    ) -> ServiceResult[ProductImage]:
        """Make this image the primary by moving it to order=0, shifting others up."""
        self._authorize(actor, "catalog", "product_image", "update")
        with self._uow_factory() as uow:
            image = uow.product_images.get(
                ProductImageFilter(id=image_id, variant_id=variant_id)
            )
            if image is None:
                raise ProductImageNotFound()
            all_images = uow.product_images.list(
                ProductImageFilter(variant_id=variant_id)
            ).items
            # Shift all images with order < current image's order up by 1
            for idx, img in enumerate(all_images):
                img.reorder(idx + 1)
                uow.product_images.update(img)
            image.reorder(0)
            image = uow.product_images.update(image)
            uow.track(image)
        return ServiceResult(data=image)

    def delete_image(
        self,
        actor: SupportsPermissionCheck,
        variant_id: uuid.UUID,
        image_id: uuid.UUID,
    ) -> ServiceResult[None]:
        self._authorize(actor, "catalog", "product_image", "delete")
        with self._uow_factory() as uow:
            image = uow.product_images.get(
                ProductImageFilter(id=image_id, variant_id=variant_id)
            )
            if image is None:
                raise ProductImageNotFound()
            image.remove()
            uow.track(image)
            self.storage.delete(image.file_path)
            uow.product_images.delete(image)
        return ServiceResult(data=None)
