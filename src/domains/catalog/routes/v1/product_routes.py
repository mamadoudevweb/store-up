"""Product routes — /api/v1/products."""
from __future__ import annotations

from uuid import UUID

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from src.app.identity import get_current_actor
from src.core.routes.envelope import EnvelopeResponse, ok
from src.domains.catalog.entities import ProductStatus
from src.domains.catalog.repositories.filters import ProductFilter
from src.domains.catalog.routes.v1.helpers import (
    _get_catalog,
    serialize_product,
    serialize_product_category,
)
from src.domains.catalog.routes.v1.schemas.product_schemas import (
    AssignCategoryRequest,
    ChangeStatusRequest,
    CreateProductRequest,
    UpdateProductRequest,
)

bp = Blueprint("product", __name__)


@bp.post("")
@jwt_required()
def create_product() -> EnvelopeResponse:
    actor = get_current_actor()
    body = CreateProductRequest.model_validate(request.get_json(force=True))
    result = _get_catalog().product.create_product(
        actor=actor,
        name=body.name,
        description=body.description,
        brand_id=body.brand_id,
        sku=body.sku,
        cost_price=body.cost_price,
        sell_price=body.sell_price,
    )
    return ok(serialize_product(result.data), status=201)


@bp.get("")
@jwt_required()
def list_products() -> EnvelopeResponse:
    actor = get_current_actor()
    brand_id_str = request.args.get("brand_id")
    filters = ProductFilter(
        page=int(request.args.get("page", 1)),
        limit=int(request.args.get("limit", 20)),
        name=request.args.get("name"),
        status=request.args.get("status"),
        sort_by=request.args.get("sort"),
        sort_desc=request.args.get("order", "asc").lower() == "desc",
        brand_id=UUID(brand_id_str) if brand_id_str else None,
    )
    result = _get_catalog().product.list_products(actor, filters)
    page = result.data
    return ok(
        data=[serialize_product(p) for p in page.items],
        meta={"page": page.page, "limit": page.limit, "total": page.total, "total_pages": page.total_pages},
    )


@bp.get("/<uuid:product_id>")
@jwt_required()
def get_product(product_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    result = _get_catalog().product.get_product(actor, product_id)
    return ok(serialize_product(result.data))


@bp.put("/<uuid:product_id>")
@jwt_required()
def update_product(product_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    body = UpdateProductRequest.model_validate(request.get_json(force=True))
    result = _get_catalog().product.update_product(
        actor=actor,
        product_id=product_id,
        name=body.name,
        description=body.description,
        brand_id=body.brand_id,
    )
    return ok(serialize_product(result.data))


@bp.patch("/<uuid:product_id>/status")
@jwt_required()
def change_product_status(product_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    body = ChangeStatusRequest.model_validate(request.get_json(force=True))
    result = _get_catalog().product.change_status(
        actor=actor, product_id=product_id, new_status=ProductStatus(body.status)
    )
    return ok(serialize_product(result.data))


@bp.delete("/<uuid:product_id>")
@jwt_required()
def delete_product(product_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    _get_catalog().product.delete_product(actor, product_id)
    return ok(None)


# ── Category assignments ───────────────────────────────────────────────────────

@bp.post("/<uuid:product_id>/categories")
@jwt_required()
def assign_category(product_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    body = AssignCategoryRequest.model_validate(request.get_json(force=True))
    result = _get_catalog().product_category.assign_category(
        actor=actor, product_id=product_id, category_id=body.category_id
    )
    return ok(serialize_product_category(result.data), status=201)


@bp.get("/<uuid:product_id>/categories")
@jwt_required()
def list_product_categories(product_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    result = _get_catalog().product_category.list_categories(actor, product_id)
    return ok([serialize_product_category(pc) for pc in result.data.items])


@bp.delete("/<uuid:product_id>/categories/<uuid:category_id>")
@jwt_required()
def unassign_category(product_id: UUID, category_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    _get_catalog().product_category.unassign_category(actor, product_id, category_id)
    return ok(None)
