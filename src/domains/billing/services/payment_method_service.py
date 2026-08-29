"""PaymentMethodService — CRUD for payment method configuration."""
from __future__ import annotations

import uuid

from src.core.entities.pagination import Pagination
from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.result import ServiceResult
from src.domains.billing.entities.payment_method import PaymentMethod
from src.domains.billing.exceptions import BillingPaymentMethodNotFoundError
from src.domains.billing.repositories.filters import PaymentMethodFilter


class PaymentMethodService(BaseService):
    def create_payment_method(
        self,
        actor: SupportsPermissionCheck,
        name: str,
        processor_key: str,
        is_active: bool = False,
    ) -> ServiceResult[PaymentMethod]:
        self._authorize(actor, "billing", "payment_method", "create")
        pm = PaymentMethod.create(name=name, processor_key=processor_key, is_active=is_active)
        with self._uow_factory() as uow:
            pm = uow.payment_methods.add(pm)
            uow.commit()
        return ServiceResult(data=pm)

    def get_payment_method(
        self,
        actor: SupportsPermissionCheck,
        payment_method_id: uuid.UUID,
    ) -> ServiceResult[PaymentMethod]:
        self._authorize(actor, "billing", "payment_method", "read")
        with self._uow_factory() as uow:
            pm = uow.payment_methods.get(payment_method_id)
        if pm is None:
            raise BillingPaymentMethodNotFoundError()
        return ServiceResult(data=pm)

    def list_payment_methods(
        self,
        actor: SupportsPermissionCheck,
        filter_: PaymentMethodFilter,
    ) -> ServiceResult[Pagination[PaymentMethod]]:
        self._authorize(actor, "billing", "payment_method", "read")
        with self._uow_factory() as uow:
            page = uow.payment_methods.list(filter_)
        return ServiceResult(data=page)

    def activate_payment_method(
        self,
        actor: SupportsPermissionCheck,
        payment_method_id: uuid.UUID,
    ) -> ServiceResult[PaymentMethod]:
        self._authorize(actor, "billing", "payment_method", "update")
        with self._uow_factory() as uow:
            pm = uow.payment_methods.get(payment_method_id)
            if pm is None:
                raise BillingPaymentMethodNotFoundError()
            pm.is_active = True
            pm = uow.payment_methods.update(pm)
            uow.commit()
        return ServiceResult(data=pm)

    def deactivate_payment_method(
        self,
        actor: SupportsPermissionCheck,
        payment_method_id: uuid.UUID,
    ) -> ServiceResult[PaymentMethod]:
        self._authorize(actor, "billing", "payment_method", "update")
        with self._uow_factory() as uow:
            pm = uow.payment_methods.get(payment_method_id)
            if pm is None:
                raise BillingPaymentMethodNotFoundError()
            pm.is_active = False
            pm = uow.payment_methods.update(pm)
            uow.commit()
        return ServiceResult(data=pm)
