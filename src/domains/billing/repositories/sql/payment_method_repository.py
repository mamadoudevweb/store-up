"""PaymentMethod SQL repository."""
from __future__ import annotations

from typing import Any

from sqlalchemy.sql import Select

from src.core.repositories.sql.base_sql_repository import BaseSqlRepository
from src.domains.billing.entities.payment_method import PaymentMethod
from src.domains.billing.repositories.filters import PaymentMethodFilter
from src.domains.billing.repositories.sql.orms import PaymentMethodModel
from src.domains.billing.repositories.sql.mappers import PaymentMethodMapper


class SqlPaymentMethodRepository(BaseSqlRepository[PaymentMethod, PaymentMethodFilter]):
    model = PaymentMethodModel
    mapper = PaymentMethodMapper()
    filter_cls = PaymentMethodFilter

    def _apply_filter(self, query: Select[Any], f: PaymentMethodFilter) -> Select[Any]:
        if f.id is not None:
            query = query.where(PaymentMethodModel.id == f.id)
        if f.name is not None:
            query = query.where(PaymentMethodModel.name == f.name)
        if f.processor_key is not None:
            query = query.where(PaymentMethodModel.processor_key == f.processor_key)
        if f.is_active is not None:
            query = query.where(PaymentMethodModel.is_active == f.is_active)
        if f.sort_by:
            col = getattr(PaymentMethodModel, f.sort_by)
            query = query.order_by(col.desc() if f.sort_desc else col.asc())
        return query
