"""ProductVariant routes — /api/v1/variants (flat, not nested under products)."""
from __future__ import annotations

from uuid import UUID

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from src.app.identity import get_current_actor
from src.core.routes.envelope import EnvelopeResponse, ok
from src.domains.catalog.entities import VariantStatus
from src.domains.catalog.repositories.filters import ProductVariantFilter
from src.domains.catalog.routes.v1.helpers import _get_catalog, serialize_product_image, serialize_variant
from src.domains.catalog.routes.v1.schemas.product_schemas import (
    ChangeStatusRequest,
    CreateVariantRequest,
    UpdateVariantRequest,
)

bp = Blueprint("product_variant", __name__)


@bp.post("")
@jwt_required()
def create_variant() -> EnvelopeResponse:
    actor = get_current_actor()
    body = CreateVariantRequest.model_validate(request.get_json(force=True))
    result = _get_catalog().variant.create_variant(
        actor=actor,
        product_id=body.product_id,
        sku=body.sku,
        cost_price=body.cost_price,
        sell_price=body.sell_price,
    )
    return ok(serialize_variant(result.data), status=201)


@bp.get("")
@jwt_required()
def list_variants() -> EnvelopeResponse:
    actor = get_current_actor()
    product_id_str = request.args.get("product_id")
    filters = ProductVariantFilter(
        page=int(request.args.get("page", 1)),
        limit=int(request.args.get("limit", 20)),
        sku=request.args.get("sku"),
        status=request.args.get("status"),
        product_id=UUID(product_id_str) if product_id_str else None,
    )
    result = _get_catalog().variant.list_variants(actor, filters)
    page = result.data
    return ok(
        data=[serialize_variant(v) for v in page.items],
        meta={"page": page.page, "limit": page.limit, "total": page.total, "total_pages": page.total_pages},
    )


@bp.get("/<uuid:variant_id>")
@jwt_required()
def get_variant(variant_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    result = _get_catalog().variant.get_variant(actor, variant_id)
    return ok(serialize_variant(result.data))


@bp.put("/<uuid:variant_id>")
@jwt_required()
def update_variant(variant_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    body = UpdateVariantRequest.model_validate(request.get_json(force=True))
    result = _get_catalog().variant.update_variant(
        actor=actor,
        variant_id=variant_id,
        sku=body.sku,
        cost_price=body.cost_price,
        sell_price=body.sell_price,
    )
    return ok(serialize_variant(result.data))


@bp.patch("/<uuid:variant_id>/status")
@jwt_required()
def change_variant_status(variant_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    body = ChangeStatusRequest.model_validate(request.get_json(force=True))
    result = _get_catalog().variant.change_status(
        actor=actor, variant_id=variant_id, new_status=VariantStatus(body.status)
    )
    return ok(serialize_variant(result.data))


@bp.delete("/<uuid:variant_id>")
@jwt_required()
def delete_variant(variant_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    _get_catalog().variant.delete_variant(actor, variant_id)
    return ok(None)


# ── Images sub-collection ─────────────────────────────────────────────────────

@bp.post("/<uuid:variant_id>/images")
@jwt_required()
def upload_variant_image(variant_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    from src.core.routes.envelope import fail
    if "file" not in request.files:
        return fail("BAD_REQUEST", "No file part provided", 400)
    file = request.files["file"]
    if not file.filename:
        return fail("BAD_REQUEST", "No selected file", 400)
    order = int(request.form.get("order", 0))
    result = _get_catalog().product_image.upload_image(
        actor=actor,
        variant_id=variant_id,
        filename=file.filename,
        file_stream=file.stream,
        order=order,
    )
    return ok(serialize_product_image(result.data), status=201)


@bp.get("/<uuid:variant_id>/images")
@jwt_required()
def list_variant_images(variant_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    result = _get_catalog().product_image.list_images(actor, variant_id)
    page = result.data
    return ok(
        data=[serialize_product_image(img) for img in page.items],
        meta={"page": page.page, "limit": page.limit, "total": page.total, "total_pages": page.total_pages},
    )


@bp.put("/<uuid:variant_id>/images/<uuid:image_id>/primary")
@jwt_required()
def set_primary_image(variant_id: UUID, image_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    result = _get_catalog().product_image.set_primary(actor, variant_id, image_id)
    return ok(serialize_product_image(result.data))


@bp.delete("/<uuid:variant_id>/images/<uuid:image_id>")
@jwt_required()
def delete_variant_image(variant_id: UUID, image_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    _get_catalog().product_image.delete_image(actor, variant_id, image_id)
    return ok(None)
