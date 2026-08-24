from src.core.docs.openapi_registry import spec
from src.domains.catalog.routes.v1.schemas.product_schemas import (
    AttributeResponse, CreateAttributeRequest,
    AttributeValueResponse, CreateAttributeValueRequest
)

def register_attribute_docs() -> None:
    auth_errors = {
        "401": {"description": "Unauthorized"},
        "403": {"description": "Forbidden"}
    }
    not_found = {
        "404": {"description": "Not Found"}
    }
    validation_errors = {
        "400": {"description": "Bad Request"},
        "422": {"description": "Validation Error"}
    }

    spec.path(
        path="/api/v1/attributes",
        operations={
            "get": {
                "tags": ["Catalog / Attributes"],
                "summary": "List attributes",
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}},
                    {"name": "name", "in": "query", "schema": {"type": "string"}},
                ],
                "responses": {
                    "200": {"description": "Paginated list of attributes"},
                    **auth_errors
                },
            },
            "post": {
                "tags": ["Catalog / Attributes"],
                "summary": "Create attribute",
                "requestBody": {"content": {"application/json": {"schema": CreateAttributeRequest.model_json_schema()}}},
                "responses": {
                    "201": {"content": {"application/json": {"schema": AttributeResponse.model_json_schema()}}},
                    **auth_errors,
                    **validation_errors
                },
            }
        }
    )

    spec.path(
        path="/api/v1/attributes/{attribute_id}",
        operations={
            "get": {
                "tags": ["Catalog / Attributes"],
                "summary": "Get attribute",
                "parameters": [{"name": "attribute_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"content": {"application/json": {"schema": AttributeResponse.model_json_schema()}}},
                    **auth_errors,
                    **not_found
                },
            }
        }
    )

    spec.path(
        path="/api/v1/attributes/{attribute_id}/values",
        operations={
            "get": {
                "tags": ["Catalog / Attributes"],
                "summary": "List attribute values",
                "parameters": [{"name": "attribute_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"description": "Paginated list of attribute values"},
                    **auth_errors,
                    **not_found
                },
            },
            "post": {
                "tags": ["Catalog / Attributes"],
                "summary": "Create attribute value",
                "parameters": [{"name": "attribute_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {"content": {"application/json": {"schema": CreateAttributeValueRequest.model_json_schema()}}},
                "responses": {
                    "201": {"content": {"application/json": {"schema": AttributeValueResponse.model_json_schema()}}},
                    **auth_errors,
                    **not_found,
                    **validation_errors
                },
            }
        }
    )
