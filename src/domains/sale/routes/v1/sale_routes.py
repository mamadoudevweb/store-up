import uuid
from flask import Blueprint, current_app
from flask_jwt_extended import jwt_required
from typing import cast

from src.app.domain_service import DomainService
from src.app.identity import get_current_actor
from src.core.routes.envelope import ok, EnvelopeResponse
from src.domains.sale.routes.v1.schemas.sale_schemas import (
    CheckoutRequest, SaleResponse
)

sale_bp = Blueprint("sales", __name__, url_prefix="/api/v1/sales")


@sale_bp.route("/checkout", methods=["POST"])
@jwt_required()
def checkout() -> EnvelopeResponse:
    from flask import request
    data = CheckoutRequest.model_validate(request.get_json())
    domain_service = cast(DomainService, current_app.extensions["domain_service"])
    actor = get_current_actor()
    
    lines_data = [line.model_dump() for line in data.lines]
    
    result = domain_service.sale.sale.checkout(
        account=actor,
        seller_account_id=data.seller_account_id,
        payment_method_id=data.payment_method_id,
        lines_data=lines_data,
        customer_name=data.customer_name,
        discount=data.discount,
    )
    
    return ok(SaleResponse.model_validate(result.data).model_dump(mode="json"), status=201)


@sale_bp.route("/<uuid:sale_id>/complete", methods=["POST"])
@jwt_required()
def complete_sale(sale_id: uuid.UUID) -> EnvelopeResponse:
    domain_service = cast(DomainService, current_app.extensions["domain_service"])
    actor = get_current_actor()
    
    result = domain_service.sale.sale.complete_sale(account=actor, sale_id=sale_id)
    return ok(SaleResponse.model_validate(result.data).model_dump(mode="json"))


@sale_bp.route("/<uuid:sale_id>/fail", methods=["POST"])
@jwt_required()
def fail_sale(sale_id: uuid.UUID) -> EnvelopeResponse:
    domain_service = cast(DomainService, current_app.extensions["domain_service"])
    actor = get_current_actor()
    
    result = domain_service.sale.sale.fail_sale(account=actor, sale_id=sale_id, reason="Payment declined")
    return ok(SaleResponse.model_validate(result.data).model_dump(mode="json"))
