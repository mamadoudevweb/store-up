from src.core.docs.openapi_registry import spec
from src.domains.catalog.routes.v1.schemas.product_schemas import (
    CategoryResponse, CreateCategoryRequest, UpdateCategoryRequest,
)

def register_category_docs() -> None:
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
        path="/api/v1/categories",
        operations={
            "get": {
                "tags": ["Catalog / Categories"],
                "summary": "List categories",
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}},
                    {"name": "name", "in": "query", "schema": {"type": "string"}},
                    {"name": "parent_id", "in": "query", "schema": {"type": "string", "format": "uuid"}},
                ],
                "responses": {
                    "200": {"description": "Paginated list of categories"},
                    **auth_errors
                },
            },
            "post": {
                "tags": ["Catalog / Categories"],
                "summary": "Create category",
                "requestBody": {"content": {"application/json": {"schema": CreateCategoryRequest.model_json_schema()}}},
                "responses": {
                    "201": {"content": {"application/json": {"schema": CategoryResponse.model_json_schema()}}},
                    **auth_errors,
                    **validation_errors
                },
            }
        }
    )

    spec.path(
        path="/api/v1/categories/{category_id}",
        operations={
            "get": {
                "tags": ["Catalog / Categories"],
                "summary": "Get category",
                "parameters": [{"name": "category_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"content": {"application/json": {"schema": CategoryResponse.model_json_schema()}}},
                    **auth_errors,
                    **not_found
                },
            },
            "put": {
                "tags": ["Catalog / Categories"],
                "summary": "Update category",
                "parameters": [{"name": "category_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {"content": {"application/json": {"schema": UpdateCategoryRequest.model_json_schema()}}},
                "responses": {
                    "200": {"content": {"application/json": {"schema": CategoryResponse.model_json_schema()}}},
                    **auth_errors,
                    **not_found,
                    **validation_errors
                },
            },
            "delete": {
                "tags": ["Catalog / Categories"],
                "summary": "Delete category",
                "parameters": [{"name": "category_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"description": "Category deleted"},
                    **auth_errors,
                    **not_found
                },
            }
        }
    )
