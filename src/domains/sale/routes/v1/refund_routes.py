from flask import Blueprint, current_app
from flask_jwt_extended import jwt_required
from typing import cast

from src.app.domain_service import DomainService
from src.app.identity import get_current_actor
from src.core.routes.envelope import ok, EnvelopeResponse
from src.domains.sale.routes.v1.schemas.sale_schemas import (
    RefundRequest, RefundResponse
)

refund_bp = Blueprint("refunds", __name__, url_prefix="/api/v1/refunds")


@refund_bp.route("", methods=["POST"])
@jwt_required()
def process_refund() -> EnvelopeResponse:
    from flask import request
    data = RefundRequest.model_validate(request.get_json())
    domain_service = cast(DomainService, current_app.extensions["domain_service"])
    actor = get_current_actor()
    
    lines_data = [line.model_dump() for line in data.lines]
    
    result = domain_service.sale.refund.request_refund(
        account=actor,
        sale_id=data.sale_id,
        processed_by=data.processed_by,
        reason=data.reason,
        lines_data=lines_data,
    )
    
    return ok(RefundResponse.model_validate(result.data).model_dump(mode="json"), status=201)
