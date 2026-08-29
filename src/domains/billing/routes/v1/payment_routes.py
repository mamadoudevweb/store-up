"""Payment routes — read and retry."""
from __future__ import annotations

import uuid
from typing import cast

from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required

from src.app.domain_service import DomainService
from src.app.identity import get_current_actor
from src.core.routes.envelope import ok, EnvelopeResponse
from src.domains.billing.routes.v1.schemas.billing_schemas import (
    PaymentResponse,
    RetryPaymentRequest,
)

payments_bp = Blueprint(
    "billing_payments",
    __name__,
    url_prefix="/api/v1/billing/payments",
)


@payments_bp.route("/sale/<uuid:sale_id>", methods=["GET"])
@jwt_required()
def list_payments_for_sale(sale_id: uuid.UUID) -> EnvelopeResponse:
    """Return all payment attempts for a given sale."""
    domain_service = cast(DomainService, current_app.extensions["domain_service"])
    actor = get_current_actor()
    result = domain_service.billing.payment.list_for_sale(actor, sale_id=sale_id)
    return ok([PaymentResponse.model_validate(p).model_dump(mode="json") for p in result.data])


@payments_bp.route("/sale/<uuid:sale_id>/retry", methods=["POST"])
@jwt_required()
def retry_payment(sale_id: uuid.UUID) -> EnvelopeResponse:
    domain_service = cast(DomainService, current_app.extensions["domain_service"])
    actor = get_current_actor()
    data = RetryPaymentRequest.model_validate(request.get_json(force=True) or {})
    result = domain_service.billing.payment.retry_payment(
        actor,
        sale_id=sale_id,
        payment_method_id=data.payment_method_id,
    )
    return ok(PaymentResponse.model_validate(result.data).model_dump(mode="json"))
