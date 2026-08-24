"""Attribute and AttributeValue service."""
from __future__ import annotations

import uuid
from typing import Callable

from src.core.repositories.base_uow import BaseUnitOfWork
from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.result import ServiceResult
from src.core.entities.pagination import Pagination
from src.domains.catalog.entities import Attribute, AttributeValue
from src.domains.catalog.exceptions import AttributeNotFound, AttributeValueNotFound
from src.domains.catalog.repositories.filters import AttributeFilter, AttributeValueFilter


class AttributeService(BaseService):
    def __init__(self, uow_factory: Callable[[], BaseUnitOfWork]) -> None:
        super().__init__(uow_factory)

    def create_attribute(
        self, actor: SupportsPermissionCheck, name: str
    ) -> ServiceResult[Attribute]:
        self._authorize(actor, "catalog", "attribute", "create")
        with self._uow_factory() as uow:
            attr = Attribute.create(name=name)
            attr = uow.attributes.add(attr)
            uow.track(attr)
        return ServiceResult(data=attr)

    def list_attributes(
        self, actor: SupportsPermissionCheck, filters: AttributeFilter
    ) -> ServiceResult[Pagination[Attribute]]:
        self._authorize(actor, "catalog", "attribute", "read")
        with self._uow_factory() as uow:
            page = uow.attributes.list(filters)
        return ServiceResult(data=page)

    def get_attribute(
        self, actor: SupportsPermissionCheck, attribute_id: uuid.UUID
    ) -> ServiceResult[Attribute]:
        self._authorize(actor, "catalog", "attribute", "read")
        with self._uow_factory() as uow:
            attr = uow.attributes.get(AttributeFilter(id=attribute_id))
        if attr is None:
            raise AttributeNotFound()
        return ServiceResult(data=attr)

    def create_value(
        self,
        actor: SupportsPermissionCheck,
        attribute_id: uuid.UUID,
        value: str,
    ) -> ServiceResult[AttributeValue]:
        self._authorize(actor, "catalog", "attribute", "create")
        with self._uow_factory() as uow:
            if uow.attributes.get(AttributeFilter(id=attribute_id)) is None:
                raise AttributeNotFound()
            av = AttributeValue.create(attribute_id=attribute_id, value=value)
            av = uow.attribute_values.add(av)
            uow.track(av)
        return ServiceResult(data=av)

    def list_values(
        self, actor: SupportsPermissionCheck, attribute_id: uuid.UUID
    ) -> ServiceResult[Pagination[AttributeValue]]:
        self._authorize(actor, "catalog", "attribute", "read")
        with self._uow_factory() as uow:
            page = uow.attribute_values.list(AttributeValueFilter(attribute_id=attribute_id))
        return ServiceResult(data=page)
