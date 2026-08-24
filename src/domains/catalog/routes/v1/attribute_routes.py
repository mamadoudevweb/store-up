"""Attribute routes — /api/v1/attributes."""
from __future__ import annotations

from uuid import UUID

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from src.app.identity import get_current_actor
from src.core.routes.envelope import EnvelopeResponse, ok
from src.domains.catalog.repositories.filters import AttributeFilter
from src.domains.catalog.routes.v1.helpers import (
    _get_catalog,
    serialize_attribute,
    serialize_attribute_value,
)
from src.domains.catalog.routes.v1.schemas.product_schemas import (
    CreateAttributeRequest,
    CreateAttributeValueRequest,
)

bp = Blueprint("attribute", __name__)


@bp.post("")
@jwt_required()
def create_attribute() -> EnvelopeResponse:
    actor = get_current_actor()
    body = CreateAttributeRequest.model_validate(request.get_json(force=True))
    result = _get_catalog().attribute.create_attribute(actor=actor, name=body.name)
    return ok(serialize_attribute(result.data), status=201)


@bp.get("")
@jwt_required()
def list_attributes() -> EnvelopeResponse:
    actor = get_current_actor()
    filters = AttributeFilter(
        page=int(request.args.get("page", 1)),
        limit=int(request.args.get("limit", 20)),
        name=request.args.get("name"),
    )
    result = _get_catalog().attribute.list_attributes(actor, filters)
    page = result.data
    return ok(
        data=[serialize_attribute(a) for a in page.items],
        meta={"page": page.page, "limit": page.limit, "total": page.total, "total_pages": page.total_pages},
    )


@bp.get("/<uuid:attribute_id>")
@jwt_required()
def get_attribute(attribute_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    result = _get_catalog().attribute.get_attribute(actor, attribute_id)
    return ok(serialize_attribute(result.data))


# ── Attribute Values ──────────────────────────────────────────────────────────

@bp.post("/<uuid:attribute_id>/values")
@jwt_required()
def create_attribute_value(attribute_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    body = CreateAttributeValueRequest.model_validate(request.get_json(force=True))
    result = _get_catalog().attribute.create_value(
        actor=actor, attribute_id=attribute_id, value=body.value
    )
    return ok(serialize_attribute_value(result.data), status=201)


@bp.get("/<uuid:attribute_id>/values")
@jwt_required()
def list_attribute_values(attribute_id: UUID) -> EnvelopeResponse:
    actor = get_current_actor()
    result = _get_catalog().attribute.list_values(actor, attribute_id)
    page = result.data
    return ok(
        data=[serialize_attribute_value(av) for av in page.items],
        meta={"page": page.page, "limit": page.limit, "total": page.total, "total_pages": page.total_pages},
    )
