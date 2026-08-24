"""Stock Item routes — /api/v1/stock/items."""
from __future__ import annotations

from uuid import UUID

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from src.app.identity import get_current_actor
from src.core.routes.envelope import ok, EnvelopeResponse
from src.domains.stock.repositories.filters import StockItemFilter
from src.domains.stock.routes.v1.helpers import _get_stock
from src.domains.stock.routes.v1.schemas.stock_schemas import (
    AdjustStockRequest,
    StockItemOutSchema,
    ReserveStockRequest,
    SetLowStockThresholdRequest,
)

bp = Blueprint("stock_item", __name__)


from typing import Any
def _serialize_item(item) -> dict[str, Any]:
    item_dict = {
        "id": str(item.id),
        "variant_id": str(item.variant_id),
        "quantity_on_hand": item.quantity_on_hand,
        "quantity_reserved": item.quantity_reserved,
        "low_stock_threshold": item.low_stock_threshold,
        "available_quantity": item.available_quantity,
    }
    return StockItemOutSchema.model_validate(item_dict).model_dump()


@bp.get("")
@jwt_required()
def list_items() -> EnvelopeResponse:
    actor = get_current_actor()
    variant_id_str = request.args.get("variant_id")
    filters = StockItemFilter(
        page=int(request.args.get("page", 1)),
        limit=int(request.args.get("limit", 20)),
        sort_by=request.args.get("sort"),
        sort_desc=request.args.get("order", "asc").lower() == "desc",
        variant_id=UUID(variant_id_str) if variant_id_str else None,
    )
    result = _get_stock().item.list_stock_items(actor, filters)
    page = result.data
    return ok(
        data=[_serialize_item(i) for i in page.items],
        meta={
            "page": page.page,
            "limit": page.limit,
            "total": page.total,
            "total_pages": page.total_pages,
        },
    )


@bp.get("/<uuid:variant_id>")
@jwt_required()
def get_item(variant_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    result = _get_stock().item.get_stock_item(actor, StockItemFilter(variant_id=variant_id))
    return ok(_serialize_item(result.data))


@bp.post("/<uuid:variant_id>/adjust")
@jwt_required()
def adjust_stock(variant_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    body = AdjustStockRequest.model_validate(request.get_json(force=True))
    result = _get_stock().item.adjust_stock(
        actor=actor,
        variant_id=variant_id,
        quantity_change=body.quantity_change,
        reason=body.reason,
        reference_type=body.reference_type,
        reference_id=body.reference_id,
    )
    return ok(_serialize_item(result.data))


@bp.post("/<uuid:variant_id>/reserve")
@jwt_required()
def reserve_stock(variant_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    body = ReserveStockRequest.model_validate(request.get_json(force=True))
    result = _get_stock().item.reserve_stock(
        actor=actor,
        variant_id=variant_id,
        quantity=body.quantity,
        reference_type=body.reference_type,
        reference_id=body.reference_id,
    )
    return ok(_serialize_item(result.data))


@bp.post("/<uuid:variant_id>/release")
@jwt_required()
def release_stock(variant_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    body = ReserveStockRequest.model_validate(request.get_json(force=True))
    result = _get_stock().item.release_stock(
        actor=actor,
        variant_id=variant_id,
        quantity=body.quantity,
        reference_type=body.reference_type,
        reference_id=body.reference_id,
    )
    return ok(_serialize_item(result.data))


@bp.post("/<uuid:variant_id>/ship")
@jwt_required()
def ship_stock(variant_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    body = ReserveStockRequest.model_validate(request.get_json(force=True))
    result = _get_stock().item.ship_stock(
        actor=actor,
        variant_id=variant_id,
        quantity=body.quantity,
        reference_type=body.reference_type,
        reference_id=body.reference_id,
    )
    return ok(_serialize_item(result.data))


@bp.put("/<uuid:variant_id>/threshold")
@jwt_required()
def set_threshold(variant_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    body = SetLowStockThresholdRequest.model_validate(request.get_json(force=True))
    result = _get_stock().item.set_low_stock_threshold(
        actor=actor,
        variant_id=variant_id,
        threshold=body.threshold,
    )
    return ok(_serialize_item(result.data))
