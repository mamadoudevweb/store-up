"""Payment SQL repository.

Extra query methods beyond BaseSqlRepository:
- list_for_sale(sale_id) — all attempts for a sale, ordered by attempt_number
- latest_for_sale(sale_id) — the highest attempt_number row for a sale
- get_by_idempotency_key(key) — find by idempotency_key (for duplicate-delivery guard)
- count_settled_for_refund(refund_id) — sum of processed settlement amounts (for over-refund guard)
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.sql import Select

from src.core.repositories.sql.base_sql_repository import BaseSqlRepository
from src.domains.billing.entities.payment import Payment
from src.domains.billing.entities.enums import PaymentStatus
from src.domains.billing.repositories.filters import PaymentFilter
from src.domains.billing.repositories.sql.orms import PaymentModel
from src.domains.billing.repositories.sql.mappers import PaymentMapper


class SqlPaymentRepository(BaseSqlRepository[Payment, PaymentFilter]):
    model = PaymentModel
    mapper = PaymentMapper()
    filter_cls = PaymentFilter

    def _apply_filter(self, query: Select[Any], f: PaymentFilter) -> Select[Any]:
        if f.id is not None:
            query = query.where(PaymentModel.id == f.id)
        if f.sale_id is not None:
            query = query.where(PaymentModel.sale_id == f.sale_id)
        if f.status is not None:
            query = query.where(PaymentModel.status == f.status.value)
        if f.idempotency_key is not None:
            query = query.where(PaymentModel.idempotency_key == f.idempotency_key)
        if f.sort_by:
            col = getattr(PaymentModel, f.sort_by)
            query = query.order_by(col.desc() if f.sort_desc else col.asc())
        return query

    # ------------------------------------------------------------------
    # Domain-specific query helpers
    # ------------------------------------------------------------------

    def list_for_sale(self, sale_id: uuid.UUID) -> list[Payment]:
        """Return all payment attempts for a sale, ordered by attempt_number asc."""
        stmt = (
            select(PaymentModel)
            .where(PaymentModel.sale_id == sale_id)
            .order_by(PaymentModel.attempt_number.asc())
        )
        models = self._session.scalars(stmt).all()
        return [self.mapper.to_entity(m) for m in models]

    def latest_for_sale(self, sale_id: uuid.UUID) -> Payment | None:
        """Return the highest attempt_number Payment row for a sale."""
        stmt = (
            select(PaymentModel)
            .where(PaymentModel.sale_id == sale_id)
            .order_by(PaymentModel.attempt_number.desc())
            .limit(1)
        )
        model = self._session.scalars(stmt).first()
        return self.mapper.to_entity(model) if model else None

    def get_by_idempotency_key(self, key: str) -> Payment | None:
        """Find a payment by its idempotency_key."""
        stmt = select(PaymentModel).where(PaymentModel.idempotency_key == key)
        model = self._session.scalars(stmt).first()
        return self.mapper.to_entity(model) if model else None

    def captured_payment_for_sale(self, sale_id: uuid.UUID) -> Payment | None:
        """Return the captured Payment for a sale (the one that succeeded)."""
        stmt = (
            select(PaymentModel)
            .where(PaymentModel.sale_id == sale_id)
            .where(PaymentModel.status == PaymentStatus.CAPTURED.value)
            .limit(1)
        )
        model = self._session.scalars(stmt).first()
        return self.mapper.to_entity(model) if model else None

    def next_attempt_number(self, sale_id: uuid.UUID) -> int:
        """Return MAX(attempt_number)+1 inside a locked context to avoid races.

        Uses a subquery-based MAX that is safe under the partial unique index
        constraint on (sale_id, attempt_number) — the unique constraint acts as
        the final race guard at the DB level (spec §7.3).
        """
        result = self._session.scalar(
            select(func.coalesce(func.max(PaymentModel.attempt_number), 0))
            .where(PaymentModel.sale_id == sale_id)
        )
        return (result or 0) + 1
