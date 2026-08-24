"""Stock Movement routes — /api/v1/stock/movements."""
from __future__ import annotations

from uuid import UUID

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from src.app.identity import get_current_actor
from src.core.routes.envelope import ok, EnvelopeResponse
from src.domains.stock.repositories.filters import StockMovementFilter
from src.domains.stock.routes.v1.helpers import _get_stock
from src.domains.stock.routes.v1.schemas.stock_schemas import StockMovementOutSchema
from src.domains.stock.entities.enums import StockMovementReason, ReferenceType


bp = Blueprint("stock_movement", __name__)


from typing import Any
def _serialize_movement(movement) -> dict[str, Any]:
    movement_dict = {
        "id": str(movement.id),
        "stock_item_id": str(movement.stock_item_id),
        "quantity_change": movement.quantity_change,
        "reason": movement.reason.value if hasattr(movement.reason, 'value') else movement.reason,
        "reference_type": movement.reference_type.value if hasattr(movement.reference_type, 'value') else movement.reference_type,
        "reference_id": movement.reference_id,
        "created_at": movement.created_at.isoformat(),
    }
    return StockMovementOutSchema.model_validate(movement_dict).model_dump()


@bp.get("")
@jwt_required()
def list_movements() -> EnvelopeResponse:
    actor = get_current_actor()
    stock_item_id_str = request.args.get("stock_item_id")
    reason = request.args.get("reason")
    ref_type = request.args.get("reference_type")
    
    filters = StockMovementFilter(
        page=int(request.args.get("page", 1)),
        limit=int(request.args.get("limit", 20)),
        sort_by=request.args.get("sort"),
        sort_desc=request.args.get("order", "desc").lower() == "desc",
        stock_item_id=UUID(stock_item_id_str) if stock_item_id_str else None,
        reason=StockMovementReason(reason) if reason else None,
        reference_type=ReferenceType(ref_type) if ref_type else None,
        reference_id=request.args.get("reference_id"),
    )
    result = _get_stock().movement.list_movements(actor, filters)
    page = result.data
    return ok(
        data=[_serialize_movement(m) for m in page.items],
        meta={
            "page": page.page,
            "limit": page.limit,
            "total": page.total,
            "total_pages": page.total_pages,
        },
    )


@bp.get("/<uuid:movement_id>")
@jwt_required()
def get_movement(movement_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    result = _get_stock().movement.get_movement(actor, StockMovementFilter(id=movement_id))
    return ok(_serialize_movement(result.data))
