"""Billing domain entity ↔ ORM model mappers."""
from __future__ import annotations

from src.core.repositories.utils import Mapper
from src.domains.billing.entities.payment_method import PaymentMethod
from src.domains.billing.entities.payment import Payment
from src.domains.billing.entities.refund_settlement import RefundSettlement
from src.domains.billing.entities.enums import PaymentStatus, RefundSettlementStatus
from src.domains.billing.repositories.sql.orms import (
    PaymentMethodModel,
    PaymentModel,
    RefundSettlementModel,
)


class PaymentMethodMapper(Mapper[PaymentMethod, PaymentMethodModel]):
    def to_entity(self, model: PaymentMethodModel) -> PaymentMethod:
        return PaymentMethod(
            id=model.id,
            name=model.name,
            processor_key=model.processor_key,
            is_active=model.is_active,
        )

    def to_model(
        self,
        entity: PaymentMethod,
        model: PaymentMethodModel | None = None,
    ) -> PaymentMethodModel:
        m = model or PaymentMethodModel()
        m.id = entity.id
        m.name = entity.name
        m.processor_key = entity.processor_key
        m.is_active = entity.is_active
        return m


class PaymentMapper(Mapper[Payment, PaymentModel]):
    def to_entity(self, model: PaymentModel) -> Payment:
        return Payment(
            id=model.id,
            sale_id=model.sale_id,
            attempt_number=model.attempt_number,
            payment_method_id=model.payment_method_id,
            processor_key=model.processor_key,
            amount=model.amount,
            status=PaymentStatus(model.status),
            processor_reference=model.processor_reference,
            idempotency_key=model.idempotency_key,
            failure_reason=model.failure_reason,
            created_at=model.created_at,
            resolved_at=model.resolved_at,
        )

    def to_model(
        self,
        entity: Payment,
        model: PaymentModel | None = None,
    ) -> PaymentModel:
        m = model or PaymentModel()
        m.id = entity.id
        m.sale_id = entity.sale_id
        m.attempt_number = entity.attempt_number
        m.payment_method_id = entity.payment_method_id
        m.processor_key = entity.processor_key
        m.amount = entity.amount
        m.status = entity.status.value
        m.processor_reference = entity.processor_reference
        m.idempotency_key = entity.idempotency_key
        m.failure_reason = entity.failure_reason
        m.created_at = entity.created_at
        m.resolved_at = entity.resolved_at
        return m


class RefundSettlementMapper(Mapper[RefundSettlement, RefundSettlementModel]):
    def to_entity(self, model: RefundSettlementModel) -> RefundSettlement:
        return RefundSettlement(
            id=model.id,
            refund_id=model.refund_id,
            payment_id=model.payment_id,
            attempt_number=model.attempt_number,
            amount=model.amount,
            processor_key=model.processor_key,
            status=RefundSettlementStatus(model.status),
            processor_reference=model.processor_reference,
            failure_reason=model.failure_reason,
            created_at=model.created_at,
            resolved_at=model.resolved_at,
        )

    def to_model(
        self,
        entity: RefundSettlement,
        model: RefundSettlementModel | None = None,
    ) -> RefundSettlementModel:
        m = model or RefundSettlementModel()
        m.id = entity.id
        m.refund_id = entity.refund_id
        m.payment_id = entity.payment_id
        m.attempt_number = entity.attempt_number
        m.amount = entity.amount
        m.processor_key = entity.processor_key
        m.status = entity.status.value
        m.processor_reference = entity.processor_reference
        m.failure_reason = entity.failure_reason
        m.created_at = entity.created_at
        m.resolved_at = entity.resolved_at
        return m
