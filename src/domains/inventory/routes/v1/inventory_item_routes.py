"""Inventory Item routes — /api/v1/inventory/items."""
from __future__ import annotations

from uuid import UUID

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from src.app.identity import get_current_actor
from src.core.routes.envelope import ok, EnvelopeResponse
from src.domains.inventory.repositories.filters import InventoryItemFilter
from src.domains.inventory.routes.v1.helpers import _get_inventory
from src.domains.inventory.routes.v1.schemas.inventory_schemas import (
    AdjustStockRequest,
    InventoryItemOutSchema,
    ReserveStockRequest,
    SetLowStockThresholdRequest,
)

bp = Blueprint("inventory_item", __name__)


from typing import Any
def _serialize_item(item) -> dict[str, Any]:
    # Convert UUIDs to strings for pydantic parsing
    item_dict = {
        "id": str(item.id),
        "product_id": str(item.product_id),
        "quantity_on_hand": item.quantity_on_hand,
        "quantity_reserved": item.quantity_reserved,
        "low_stock_threshold": item.low_stock_threshold,
        "available_quantity": item.available_quantity,
    }
    return InventoryItemOutSchema.model_validate(item_dict).model_dump()


@bp.get("")
@jwt_required()
def list_items() -> EnvelopeResponse:
    actor = get_current_actor()
    product_id_str = request.args.get("product_id")
    filters = InventoryItemFilter(
        page=int(request.args.get("page", 1)),
        limit=int(request.args.get("limit", 20)),
        sort_by=request.args.get("sort"),
        sort_desc=request.args.get("order", "asc").lower() == "desc",
        product_id=UUID(product_id_str) if product_id_str else None,
    )
    result = _get_inventory().item.list_inventory_items(actor, filters)
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


@bp.get("/<uuid:product_id>")
@jwt_required()
def get_item(product_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    result = _get_inventory().item.get_inventory_item(actor, InventoryItemFilter(product_id=product_id))
    return ok(_serialize_item(result.data))


@bp.post("/<uuid:product_id>/adjust")
@jwt_required()
def adjust_stock(product_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    body = AdjustStockRequest.model_validate(request.get_json(force=True))
    result = _get_inventory().item.adjust_stock(
        actor=actor,
        product_id=product_id,
        quantity_change=body.quantity_change,
        reason=body.reason,
        reference_id=body.reference_id,
    )
    return ok(_serialize_item(result.data))


@bp.post("/<uuid:product_id>/reserve")
@jwt_required()
def reserve_stock(product_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    body = ReserveStockRequest.model_validate(request.get_json(force=True))
    result = _get_inventory().item.reserve_stock(
        actor=actor,
        product_id=product_id,
        quantity=body.quantity,
        reference_id=body.reference_id,
    )
    return ok(_serialize_item(result.data))


@bp.post("/<uuid:product_id>/release")
@jwt_required()
def release_stock(product_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    body = ReserveStockRequest.model_validate(request.get_json(force=True))
    result = _get_inventory().item.release_stock(
        actor=actor,
        product_id=product_id,
        quantity=body.quantity,
        reference_id=body.reference_id,
    )
    return ok(_serialize_item(result.data))


@bp.post("/<uuid:product_id>/ship")
@jwt_required()
def ship_stock(product_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    body = ReserveStockRequest.model_validate(request.get_json(force=True))
    result = _get_inventory().item.ship_stock(
        actor=actor,
        product_id=product_id,
        quantity=body.quantity,
        reference_id=body.reference_id,
    )
    return ok(_serialize_item(result.data))


@bp.put("/<uuid:product_id>/threshold")
@jwt_required()
def set_threshold(product_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    body = SetLowStockThresholdRequest.model_validate(request.get_json(force=True))
    result = _get_inventory().item.set_low_stock_threshold(
        actor=actor,
        product_id=product_id,
        threshold=body.threshold,
    )
    return ok(_serialize_item(result.data))
