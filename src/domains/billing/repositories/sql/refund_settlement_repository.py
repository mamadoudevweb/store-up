"""RefundSettlement SQL repository."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.sql import Select

from src.core.repositories.sql.base_sql_repository import BaseSqlRepository
from src.domains.billing.entities.refund_settlement import RefundSettlement
from src.domains.billing.entities.enums import RefundSettlementStatus
from src.domains.billing.repositories.filters import RefundSettlementFilter
from src.domains.billing.repositories.sql.orms import RefundSettlementModel
from src.domains.billing.repositories.sql.mappers import RefundSettlementMapper


class SqlRefundSettlementRepository(
    BaseSqlRepository[RefundSettlement, RefundSettlementFilter]
):
    model = RefundSettlementModel
    mapper = RefundSettlementMapper()
    filter_cls = RefundSettlementFilter

    def _apply_filter(self, query: Select[Any], f: RefundSettlementFilter) -> Select[Any]:
        if f.id is not None:
            query = query.where(RefundSettlementModel.id == f.id)
        if f.refund_id is not None:
            query = query.where(RefundSettlementModel.refund_id == f.refund_id)
        if f.payment_id is not None:
            query = query.where(RefundSettlementModel.payment_id == f.payment_id)
        if f.status is not None:
            query = query.where(RefundSettlementModel.status == f.status.value)
        if f.sort_by:
            col = getattr(RefundSettlementModel, f.sort_by)
            query = query.order_by(col.desc() if f.sort_desc else col.asc())
        return query

    # ------------------------------------------------------------------
    # Domain-specific query helpers
    # ------------------------------------------------------------------

    def latest_for_refund(self, refund_id: uuid.UUID) -> RefundSettlement | None:
        """Return the highest attempt_number RefundSettlement row for a refund."""
        stmt = (
            select(RefundSettlementModel)
            .where(RefundSettlementModel.refund_id == refund_id)
            .order_by(RefundSettlementModel.attempt_number.desc())
            .limit(1)
        )
        model = self._session.scalars(stmt).first()
        return self.mapper.to_entity(model) if model else None

    def total_settled_for_refund(self, refund_id: uuid.UUID) -> int:
        """Sum of amounts for all processed settlements for a refund_id."""
        result = self._session.scalar(
            select(func.coalesce(func.sum(RefundSettlementModel.amount), 0))
            .where(RefundSettlementModel.refund_id == refund_id)
            .where(RefundSettlementModel.status == RefundSettlementStatus.PROCESSED.value)
        )
        return int(result or 0)

    def next_attempt_number(self, refund_id: uuid.UUID) -> int:
        """Return MAX(attempt_number)+1 for a given refund_id."""
        result = self._session.scalar(
            select(func.coalesce(func.max(RefundSettlementModel.attempt_number), 0))
            .where(RefundSettlementModel.refund_id == refund_id)
        )
        return (result or 0) + 1
