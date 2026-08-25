from src.core.docs.openapi_registry import spec
from src.domains.catalog.routes.v1.schemas.product_schemas import (
    BrandResponse, CreateBrandRequest, UpdateBrandRequest,
)

def register_brand_docs() -> None:
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
        path="/api/v1/brands",
        operations={
            "get": {
                "tags": ["Catalog / Brands"],
                "summary": "List brands",
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}},
                    {"name": "name", "in": "query", "schema": {"type": "string"}},
                    {"name": "is_active", "in": "query", "schema": {"type": "boolean"}},
                ],
                "responses": {
                    "200": {"description": "Paginated list of brands"},
                    **auth_errors
                },
            },
            "post": {
                "tags": ["Catalog / Brands"],
                "summary": "Create brand",
                "requestBody": {"content": {"application/json": {"schema": CreateBrandRequest.model_json_schema()}}},
                "responses": {
                    "201": {"content": {"application/json": {"schema": BrandResponse.model_json_schema()}}},
                    **auth_errors,
                    **validation_errors
                },
            }
        }
    )

    spec.path(
        path="/api/v1/brands/{brand_id}",
        operations={
            "get": {
                "tags": ["Catalog / Brands"],
                "summary": "Get brand",
                "parameters": [{"name": "brand_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"content": {"application/json": {"schema": BrandResponse.model_json_schema()}}},
                    **auth_errors,
                    **not_found
                },
            },
            "put": {
                "tags": ["Catalog / Brands"],
                "summary": "Update brand",
                "parameters": [{"name": "brand_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {"content": {"application/json": {"schema": UpdateBrandRequest.model_json_schema()}}},
                "responses": {
                    "200": {"content": {"application/json": {"schema": BrandResponse.model_json_schema()}}},
                    **auth_errors,
                    **not_found,
                    **validation_errors
                },
            },
            "delete": {
                "tags": ["Catalog / Brands"],
                "summary": "Delete brand",
                "parameters": [{"name": "brand_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"description": "Brand deleted"},
                    **auth_errors,
                    **not_found
                },
            }
        }
    )

    spec.path(
        path="/api/v1/brands/{brand_id}/logo",
        operations={
            "post": {
                "tags": ["Catalog / Brands"],
                "summary": "Upload brand logo",
                "parameters": [{"name": "brand_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "file": {"type": "string", "format": "binary"}
                                },
                                "required": ["file"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"content": {"application/json": {"schema": BrandResponse.model_json_schema()}}},
                    **auth_errors,
                    **not_found,
                    **validation_errors
                },
            },
            "delete": {
                "tags": ["Catalog / Brands"],
                "summary": "Delete brand logo",
                "parameters": [{"name": "brand_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"content": {"application/json": {"schema": BrandResponse.model_json_schema()}}},
                    **auth_errors,
                    **not_found
                },
            }
        }
    )
