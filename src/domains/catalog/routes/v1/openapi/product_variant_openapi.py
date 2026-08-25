from src.core.docs.openapi_registry import spec
from src.domains.catalog.routes.v1.schemas.product_schemas import (
    ProductVariantResponse, CreateVariantRequest, UpdateVariantRequest,
    ChangeStatusRequest, ProductImageResponse
)

def register_variant_docs() -> None:
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
        path="/api/v1/variants",
        operations={
            "get": {
                "tags": ["Catalog / Product Variants"],
                "summary": "List product variants",
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}},
                    {"name": "sku", "in": "query", "schema": {"type": "string"}},
                    {"name": "status", "in": "query", "schema": {"type": "string", "enum": ["active", "archived"]}},
                    {"name": "product_id", "in": "query", "schema": {"type": "string", "format": "uuid"}},
                ],
                "responses": {
                    "200": {"description": "Paginated list of product variants"},
                    **auth_errors
                },
            },
            "post": {
                "tags": ["Catalog / Product Variants"],
                "summary": "Create product variant",
                "requestBody": {"content": {"application/json": {"schema": CreateVariantRequest.model_json_schema()}}},
                "responses": {
                    "201": {"content": {"application/json": {"schema": ProductVariantResponse.model_json_schema()}}},
                    **auth_errors,
                    **validation_errors
                },
            }
        }
    )

    spec.path(
        path="/api/v1/variants/{variant_id}",
        operations={
            "get": {
                "tags": ["Catalog / Product Variants"],
                "summary": "Get product variant",
                "parameters": [{"name": "variant_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"content": {"application/json": {"schema": ProductVariantResponse.model_json_schema()}}},
                    **auth_errors,
                    **not_found
                },
            },
            "put": {
                "tags": ["Catalog / Product Variants"],
                "summary": "Update product variant",
                "parameters": [{"name": "variant_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {"content": {"application/json": {"schema": UpdateVariantRequest.model_json_schema()}}},
                "responses": {
                    "200": {"content": {"application/json": {"schema": ProductVariantResponse.model_json_schema()}}},
                    **auth_errors,
                    **not_found,
                    **validation_errors
                },
            },
            "delete": {
                "tags": ["Catalog / Product Variants"],
                "summary": "Delete product variant",
                "parameters": [{"name": "variant_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"description": "Product variant deleted"},
                    **auth_errors,
                    **not_found
                },
            }
        }
    )

    spec.path(
        path="/api/v1/variants/{variant_id}/status",
        operations={
            "patch": {
                "tags": ["Catalog / Product Variants"],
                "summary": "Change product variant status",
                "parameters": [{"name": "variant_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {"content": {"application/json": {"schema": ChangeStatusRequest.model_json_schema()}}},
                "responses": {
                    "200": {"content": {"application/json": {"schema": ProductVariantResponse.model_json_schema()}}},
                    **auth_errors,
                    **not_found,
                    **validation_errors
                },
            }
        }
    )

    spec.path(
        path="/api/v1/variants/{variant_id}/images",
        operations={
            "get": {
                "tags": ["Catalog / Product Variants"],
                "summary": "List product variant images",
                "parameters": [{"name": "variant_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"description": "Paginated list of product variant images"},
                    **auth_errors,
                    **not_found
                },
            },
            "post": {
                "tags": ["Catalog / Product Variants"],
                "summary": "Upload product variant image",
                "parameters": [{"name": "variant_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "file": {"type": "string", "format": "binary"},
                                    "order": {"type": "integer"}
                                },
                                "required": ["file"]
                            }
                        }
                    }
                },
                "responses": {
                    "201": {"content": {"application/json": {"schema": ProductImageResponse.model_json_schema()}}},
                    **auth_errors,
                    **not_found,
                    **validation_errors
                },
            }
        }
    )

    spec.path(
        path="/api/v1/variants/{variant_id}/images/{image_id}/primary",
        operations={
            "put": {
                "tags": ["Catalog / Product Variants"],
                "summary": "Set primary image",
                "parameters": [
                    {"name": "variant_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}},
                    {"name": "image_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}
                ],
                "responses": {
                    "200": {"content": {"application/json": {"schema": ProductImageResponse.model_json_schema()}}},
                    **auth_errors,
                    **not_found
                },
            }
        }
    )

    spec.path(
        path="/api/v1/variants/{variant_id}/images/{image_id}",
        operations={
            "delete": {
                "tags": ["Catalog / Product Variants"],
                "summary": "Delete image",
                "parameters": [
                    {"name": "variant_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}},
                    {"name": "image_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}
                ],
                "responses": {
                    "200": {"description": "Image deleted"},
                    **auth_errors,
                    **not_found
                },
            }
        }
    )
