"""Brand routes — /api/v1/brands."""
from __future__ import annotations

from uuid import UUID

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from src.app.identity import get_current_actor
from src.core.routes.envelope import ok
from src.domains.catalog.repositories.filters import BrandFilter
from src.domains.catalog.routes.v1.helpers import _get_catalog, serialize_brand
from src.domains.catalog.routes.v1.schemas.product_schemas import (
    CreateBrandRequest,
    UpdateBrandRequest,
)

bp = Blueprint("brand", __name__)


@bp.post("")
@jwt_required()
def create_brand():  # type: ignore[no-untyped-def]
    actor = get_current_actor()
    body = CreateBrandRequest.model_validate(request.get_json(force=True))
    result = _get_catalog().brand.create_brand(
        actor=actor,
        name=body.name,
        description=body.description,
    )
    return ok(serialize_brand(result.data), status=201)


@bp.get("")
@jwt_required()
def list_brands():  # type: ignore[no-untyped-def]
    actor = get_current_actor()
    is_active_str = request.args.get("is_active")
    filters = BrandFilter(
        page=int(request.args.get("page", 1)),
        limit=int(request.args.get("limit", 20)),
        name=request.args.get("name"),
        is_active=is_active_str.lower() in ("true", "1", "yes") if is_active_str else None,
    )
    result = _get_catalog().brand.list_brands(actor, filters)
    page = result.data
    return ok(
        data=[serialize_brand(b) for b in page.items],
        meta={
            "page": page.page,
            "limit": page.limit,
            "total": page.total,
            "total_pages": page.total_pages,
        },
    )


@bp.get("/<uuid:brand_id>")
@jwt_required()
def get_brand(brand_id: UUID):  # type: ignore[no-untyped-def]
    actor = get_current_actor()
    result = _get_catalog().brand.get_brand(actor, brand_id)
    return ok(serialize_brand(result.data))


@bp.put("/<uuid:brand_id>")
@jwt_required()
def update_brand(brand_id: UUID):  # type: ignore[no-untyped-def]
    actor = get_current_actor()
    body = UpdateBrandRequest.model_validate(request.get_json(force=True))
    result = _get_catalog().brand.update_brand(
        actor=actor,
        brand_id=brand_id,
        name=body.name,
        description=body.description,
    )
    return ok(serialize_brand(result.data))


@bp.delete("/<uuid:brand_id>")
@jwt_required()
def delete_brand(brand_id: UUID):  # type: ignore[no-untyped-def]
    actor = get_current_actor()
    _get_catalog().brand.delete_brand(actor, brand_id)
    return ok(None)


@bp.post("/<uuid:brand_id>/logo")
@jwt_required()
def upload_logo(brand_id: UUID):  # type: ignore[no-untyped-def]
    actor = get_current_actor()
    if "file" not in request.files:
        from src.core.routes.envelope import fail
        return fail("BAD_REQUEST", "No file part provided", 400)
    file = request.files["file"]
    if not file.filename:
        from src.core.routes.envelope import fail
        return fail("BAD_REQUEST", "No selected file", 400)
    result = _get_catalog().brand.upload_logo(actor, brand_id, file.filename, file.stream)
    return ok(serialize_brand(result.data))


@bp.delete("/<uuid:brand_id>/logo")
@jwt_required()
def delete_logo(brand_id: UUID):  # type: ignore[no-untyped-def]
    actor = get_current_actor()
    result = _get_catalog().brand.delete_logo(actor, brand_id)
    return ok(serialize_brand(result.data))
