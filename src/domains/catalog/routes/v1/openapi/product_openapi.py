from src.core.docs.openapi_registry import spec
from src.domains.catalog.routes.v1.schemas.product_schemas import (
    ProductResponse, CreateProductRequest, UpdateProductRequest,
    ChangeStatusRequest, AssignCategoryRequest, ProductCategoryResponse
)

def register_product_docs() -> None:
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
        path="/api/v1/products",
        operations={
            "get": {
                "tags": ["Catalog / Products"],
                "summary": "List products",
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}},
                    {"name": "name", "in": "query", "schema": {"type": "string"}},
                    {"name": "status", "in": "query", "schema": {"type": "string", "enum": ["draft", "active", "archived"]}},
                    {"name": "sort", "in": "query", "schema": {"type": "string"}},
                    {"name": "order", "in": "query", "schema": {"type": "string", "enum": ["asc", "desc"], "default": "asc"}},
                    {"name": "brand_id", "in": "query", "schema": {"type": "string", "format": "uuid"}},
                ],
                "responses": {
                    "200": {"description": "Paginated list of products"},
                    **auth_errors
                },
            },
            "post": {
                "tags": ["Catalog / Products"],
                "summary": "Create product",
                "requestBody": {"content": {"application/json": {"schema": CreateProductRequest.model_json_schema()}}},
                "responses": {
                    "201": {"content": {"application/json": {"schema": ProductResponse.model_json_schema()}}},
                    **auth_errors,
                    **validation_errors
                },
            }
        }
    )

    spec.path(
        path="/api/v1/products/{product_id}",
        operations={
            "get": {
                "tags": ["Catalog / Products"],
                "summary": "Get product",
                "parameters": [{"name": "product_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"content": {"application/json": {"schema": ProductResponse.model_json_schema()}}},
                    **auth_errors,
                    **not_found
                },
            },
            "put": {
                "tags": ["Catalog / Products"],
                "summary": "Update product",
                "parameters": [{"name": "product_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {"content": {"application/json": {"schema": UpdateProductRequest.model_json_schema()}}},
                "responses": {
                    "200": {"content": {"application/json": {"schema": ProductResponse.model_json_schema()}}},
                    **auth_errors,
                    **not_found,
                    **validation_errors
                },
            },
            "delete": {
                "tags": ["Catalog / Products"],
                "summary": "Delete product",
                "parameters": [{"name": "product_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"description": "Product deleted"},
                    **auth_errors,
                    **not_found
                },
            }
        }
    )

    spec.path(
        path="/api/v1/products/{product_id}/status",
        operations={
            "patch": {
                "tags": ["Catalog / Products"],
                "summary": "Change product status",
                "parameters": [{"name": "product_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {"content": {"application/json": {"schema": ChangeStatusRequest.model_json_schema()}}},
                "responses": {
                    "200": {"content": {"application/json": {"schema": ProductResponse.model_json_schema()}}},
                    **auth_errors,
                    **not_found,
                    **validation_errors
                },
            }
        }
    )

    spec.path(
        path="/api/v1/products/{product_id}/categories",
        operations={
            "get": {
                "tags": ["Catalog / Products"],
                "summary": "List product categories",
                "parameters": [{"name": "product_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"description": "List of categories assigned to the product"},
                    **auth_errors,
                    **not_found
                },
            },
            "post": {
                "tags": ["Catalog / Products"],
                "summary": "Assign category to product",
                "parameters": [{"name": "product_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {"content": {"application/json": {"schema": AssignCategoryRequest.model_json_schema()}}},
                "responses": {
                    "201": {"content": {"application/json": {"schema": ProductCategoryResponse.model_json_schema()}}},
                    **auth_errors,
                    **not_found,
                    **validation_errors
                },
            }
        }
    )

    spec.path(
        path="/api/v1/products/{product_id}/categories/{category_id}",
        operations={
            "delete": {
                "tags": ["Catalog / Products"],
                "summary": "Unassign category from product",
                "parameters": [
                    {"name": "product_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}},
                    {"name": "category_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}
                ],
                "responses": {
                    "200": {"description": "Category unassigned"},
                    **auth_errors,
                    **not_found
                },
            }
        }
    )
