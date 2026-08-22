"""Category routes — /api/v1/categories."""
from __future__ import annotations

from uuid import UUID

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from src.app.identity import get_current_actor
from src.core.routes.envelope import ok, EnvelopeResponse
from src.domains.catalog.repositories.filters import CategoryFilter
from src.domains.catalog.routes.v1.helpers import _get_catalog, serialize_category
from src.domains.catalog.routes.v1.schemas.product_schemas import (
    CreateCategoryRequest,
    UpdateCategoryRequest,
)

bp = Blueprint("category", __name__)


@bp.post("")
@jwt_required()
def create_category() -> EnvelopeResponse:
    actor = get_current_actor()
    body = CreateCategoryRequest.model_validate(request.get_json(force=True))
    result = _get_catalog().category.create_category(
        actor=actor,
        name=body.name,
        parent_id=body.parent_id,
    )
    return ok(serialize_category(result.data), status=201)


@bp.get("")
@jwt_required()
def list_categories() -> EnvelopeResponse:
    actor = get_current_actor()
    parent_id_str = request.args.get("parent_id")
    filters = CategoryFilter(
        page=int(request.args.get("page", 1)),
        limit=int(request.args.get("limit", 20)),
        name=request.args.get("name"),
        parent_id=UUID(parent_id_str) if parent_id_str else None,
    )
    result = _get_catalog().category.list_categories(actor, filters)
    page = result.data
    return ok(
        data=[serialize_category(c) for c in page.items],
        meta={
            "page": page.page,
            "limit": page.limit,
            "total": page.total,
            "total_pages": page.total_pages,
        },
    )


@bp.get("/<uuid:category_id>")
@jwt_required()
def get_category(category_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    result = _get_catalog().category.get_category(actor, category_id)
    return ok(serialize_category(result.data))


@bp.put("/<uuid:category_id>")
@jwt_required()
def update_category(category_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    body = UpdateCategoryRequest.model_validate(request.get_json(force=True))
    result = _get_catalog().category.update_category(
        actor=actor,
        category_id=category_id,
        name=body.name,
        parent_id=body.parent_id,
    )
    return ok(serialize_category(result.data))


@bp.delete("/<uuid:category_id>")
@jwt_required()
def delete_category(category_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    _get_catalog().category.delete_category(actor, category_id)
    return ok(None)
