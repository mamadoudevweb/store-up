"""Stock Movement routes — /api/v1/inventory/movements."""
from __future__ import annotations

from uuid import UUID

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from src.app.identity import get_current_actor
from src.core.routes.envelope import ok, EnvelopeResponse
from src.domains.inventory.repositories.filters import StockMovementFilter
from src.domains.inventory.routes.v1.helpers import _get_inventory
from src.domains.inventory.routes.v1.schemas.inventory_schemas import StockMovementOutSchema

bp = Blueprint("stock_movement", __name__)


from typing import Any
def _serialize_movement(movement) -> dict[str, Any]:
    mov_dict = {
        "id": str(movement.id),
        "product_id": str(movement.product_id),
        "quantity_change": movement.quantity_change,
        "reason": movement.reason,
        "reference_id": movement.reference_id,
        "created_at": movement.created_at.isoformat(),
    }
    return StockMovementOutSchema.model_validate(mov_dict).model_dump()


@bp.get("")
@jwt_required()
def list_movements() -> EnvelopeResponse:
    actor = get_current_actor()
    product_id_str = request.args.get("product_id")
    filters = StockMovementFilter(
        page=int(request.args.get("page", 1)),
        limit=int(request.args.get("limit", 20)),
        sort_by=request.args.get("sort"),
        sort_desc=request.args.get("order", "asc").lower() == "desc",
        product_id=UUID(product_id_str) if product_id_str else None,
        reason=request.args.get("reason"),
        reference_id=request.args.get("reference_id"),
    )
    result = _get_inventory().movement.list_movements(actor, filters)
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
    result = _get_inventory().movement.get_movement(actor, movement_id)
    return ok(_serialize_movement(result.data))
