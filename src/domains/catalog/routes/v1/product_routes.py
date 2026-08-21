"""Product routes — /api/v1/products."""
from __future__ import annotations

from uuid import UUID

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from src.app.identity import get_current_actor
from src.core.routes.envelope import fail, ok
from src.domains.catalog.repositories.filters import ProductFilter
from src.domains.catalog.routes.v1.helpers import (
    _get_catalog,
    serialize_product,
    serialize_product_image,
)
from src.domains.catalog.routes.v1.schemas.product_schemas import (
    CreateProductRequest,
    UpdateProductRequest,
)

bp = Blueprint("product", __name__)


# ── Products ──────────────────────────────────────────────────────────────────

@bp.post("")
@jwt_required()
def create_product():  # type: ignore[no-untyped-def]
    actor = get_current_actor()
    body = CreateProductRequest.model_validate(request.get_json(force=True))
    result = _get_catalog().product.create_product(
        actor=actor,
        sku=body.sku,
        name=body.name,
        cost_price=body.cost_price,
        sell_price=body.sell_price,
        description=body.description,
        category_id=body.category_id,
        brand_id=body.brand_id,
    )
    return ok(serialize_product(result.data), status=201)


@bp.get("")
@jwt_required()
def list_products():  # type: ignore[no-untyped-def]
    actor = get_current_actor()
    category_id_str = request.args.get("category_id")
    brand_id_str = request.args.get("brand_id")
    is_active_str = request.args.get("is_active")
    filters = ProductFilter(
        page=int(request.args.get("page", 1)),
        limit=int(request.args.get("limit", 20)),
        name=request.args.get("name"),
        sku=request.args.get("sku"),
        sort_by=request.args.get("sort"),
        sort_desc=request.args.get("order", "asc").lower() == "desc",
        category_id=UUID(category_id_str) if category_id_str else None,
        brand_id=UUID(brand_id_str) if brand_id_str else None,
        is_active=is_active_str.lower() in ("true", "1", "yes") if is_active_str is not None else None,
    )
    result = _get_catalog().product.list_products(actor, filters)
    page = result.data
    return ok(
        data=[serialize_product(p) for p in page.items],
        meta={
            "page": page.page,
            "limit": page.limit,
            "total": page.total,
            "total_pages": page.total_pages,
        },
    )


@bp.get("/<uuid:product_id>")
@jwt_required()
def get_product(product_id: UUID):  # type: ignore[no-untyped-def]
    actor = get_current_actor()
    result = _get_catalog().product.get_product(actor, product_id)
    return ok(serialize_product(result.data))


@bp.put("/<uuid:product_id>")
@jwt_required()
def update_product(product_id: UUID):  # type: ignore[no-untyped-def]
    actor = get_current_actor()
    body = UpdateProductRequest.model_validate(request.get_json(force=True))
    result = _get_catalog().product.update_product(
        actor=actor,
        product_id=product_id,
        sku=body.sku,
        name=body.name,
        cost_price=body.cost_price,
        sell_price=body.sell_price,
        description=body.description,
        category_id=body.category_id,
        brand_id=body.brand_id,
        is_active=body.is_active,
    )
    return ok(serialize_product(result.data))


@bp.delete("/<uuid:product_id>")
@jwt_required()
def delete_product(product_id: UUID):  # type: ignore[no-untyped-def]
    actor = get_current_actor()
    _get_catalog().product.delete_product(actor, product_id)
    return ok(None)


# ── Product Images ────────────────────────────────────────────────────────────

@bp.post("/<uuid:product_id>/images")
@jwt_required()
def upload_product_image(product_id: UUID):  # type: ignore[no-untyped-def]
    actor = get_current_actor()
    if "file" not in request.files:
        return fail("BAD_REQUEST", "No file part provided", 400)
    file = request.files["file"]
    if not file.filename:
        return fail("BAD_REQUEST", "No selected file", 400)
    is_primary = request.form.get("is_primary", "false").lower() in ("true", "1", "yes")
    sort_order = int(request.form.get("sort_order", 0))
    result = _get_catalog().product_image.upload_image(
        actor=actor,
        product_id=product_id,
        filename=file.filename,
        file_stream=file.stream,
        is_primary=is_primary,
        sort_order=sort_order,
    )
    return ok(serialize_product_image(result.data), status=201)


@bp.get("/<uuid:product_id>/images")
@jwt_required()
def list_product_images(product_id: UUID):  # type: ignore[no-untyped-def]
    actor = get_current_actor()
    result = _get_catalog().product_image.list_images(actor, product_id)
    page = result.data
    return ok(
        data=[serialize_product_image(img) for img in page.items],
        meta={
            "page": page.page,
            "limit": page.limit,
            "total": page.total,
            "total_pages": page.total_pages,
        },
    )


@bp.put("/<uuid:product_id>/images/<uuid:image_id>/primary")
@jwt_required()
def set_primary_image(product_id: UUID, image_id: UUID):  # type: ignore[no-untyped-def]
    actor = get_current_actor()
    result = _get_catalog().product_image.set_primary(actor, product_id, image_id)
    return ok(serialize_product_image(result.data))


@bp.delete("/<uuid:product_id>/images/<uuid:image_id>")
@jwt_required()
def delete_product_image(product_id: UUID, image_id: UUID):  # type: ignore[no-untyped-def]
    actor = get_current_actor()
    _get_catalog().product_image.delete_image(actor, product_id, image_id)
    return ok(None)
