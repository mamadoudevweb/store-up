"""PaymentMethod routes."""
from __future__ import annotations

import uuid
from typing import cast

from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required

from src.app.domain_service import DomainService
from src.app.identity import get_current_actor
from src.core.routes.envelope import ok, EnvelopeResponse
from src.domains.billing.routes.v1.schemas.billing_schemas import (
    PaymentMethodCreate,
    PaymentMethodResponse,
)
from src.domains.billing.repositories.filters import PaymentMethodFilter

payment_methods_bp = Blueprint(
    "billing_payment_methods",
    __name__,
    url_prefix="/api/v1/billing/payment-methods",
)


@payment_methods_bp.route("/", methods=["GET"])
@jwt_required()
def list_payment_methods() -> EnvelopeResponse:
    domain_service = cast(DomainService, current_app.extensions["domain_service"])
    actor = get_current_actor()
    page = int(request.args.get("page", 1, type=int))
    limit = int(request.args.get("limit", 20, type=int))
    is_active_str = request.args.get("is_active")
    is_active: bool | None = None
    if is_active_str is not None:
        is_active = is_active_str.lower() in ("true", "1", "yes")

    result = domain_service.billing.payment_method.list_payment_methods(
        actor,
        PaymentMethodFilter(page=page, limit=limit, is_active=is_active),
    )
    items = [PaymentMethodResponse.model_validate(pm).model_dump(mode="json") for pm in result.data.items]
    return ok(items, meta={"total": result.data.total, "page": result.data.page, "limit": result.data.limit})


@payment_methods_bp.route("/", methods=["POST"])
@jwt_required()
def create_payment_method() -> EnvelopeResponse:
    domain_service = cast(DomainService, current_app.extensions["domain_service"])
    actor = get_current_actor()
    data = PaymentMethodCreate.model_validate(request.get_json(force=True))
    result = domain_service.billing.payment_method.create_payment_method(
        actor,
        name=data.name,
        processor_key=data.processor_key,
        is_active=data.is_active,
    )
    return ok(PaymentMethodResponse.model_validate(result.data).model_dump(mode="json"), status=201)


@payment_methods_bp.route("/<uuid:payment_method_id>", methods=["GET"])
@jwt_required()
def get_payment_method(payment_method_id: uuid.UUID) -> EnvelopeResponse:
    domain_service = cast(DomainService, current_app.extensions["domain_service"])
    actor = get_current_actor()
    result = domain_service.billing.payment_method.get_payment_method(actor, payment_method_id)
    return ok(PaymentMethodResponse.model_validate(result.data).model_dump(mode="json"))


@payment_methods_bp.route("/<uuid:payment_method_id>/activate", methods=["POST"])
@jwt_required()
def activate_payment_method(payment_method_id: uuid.UUID) -> EnvelopeResponse:
    domain_service = cast(DomainService, current_app.extensions["domain_service"])
    actor = get_current_actor()
    result = domain_service.billing.payment_method.activate_payment_method(actor, payment_method_id)
    return ok(PaymentMethodResponse.model_validate(result.data).model_dump(mode="json"))


@payment_methods_bp.route("/<uuid:payment_method_id>/deactivate", methods=["POST"])
@jwt_required()
def deactivate_payment_method(payment_method_id: uuid.UUID) -> EnvelopeResponse:
    domain_service = cast(DomainService, current_app.extensions["domain_service"])
    actor = get_current_actor()
    result = domain_service.billing.payment_method.deactivate_payment_method(actor, payment_method_id)
    return ok(PaymentMethodResponse.model_validate(result.data).model_dump(mode="json"))
