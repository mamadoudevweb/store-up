from src.core.docs.openapi_registry import spec
from src.domains.stock.routes.v1.schemas.stock_schemas import (
    StockItemOutSchema,
    AdjustStockRequest,
    ReserveStockRequest,
    SetLowStockThresholdRequest
)

def register_stock_item_docs() -> None:
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
        path="/api/v1/stock/items",
        operations={
            "get": {
                "tags": ["Stock / Items"],
                "summary": "List stock items",
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}},
                    {"name": "variant_id", "in": "query", "schema": {"type": "string", "format": "uuid"}},
                    {"name": "sort", "in": "query", "schema": {"type": "string"}},
                    {"name": "order", "in": "query", "schema": {"type": "string", "enum": ["asc", "desc"], "default": "asc"}},
                ],
                "responses": {
                    "200": {"description": "Paginated list of stock items"},
                    **auth_errors
                },
            }
        }
    )

    spec.path(
        path="/api/v1/stock/items/{variant_id}",
        operations={
            "get": {
                "tags": ["Stock / Items"],
                "summary": "Get stock item by variant",
                "parameters": [{"name": "variant_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {
                        "description": "Stock item details",
                        "content": {"application/json": {"schema": StockItemOutSchema.model_json_schema()}}
                    },
                    **auth_errors,
                    **not_found
                },
            }
        }
    )

    spec.path(
        path="/api/v1/stock/items/{variant_id}/adjust",
        operations={
            "post": {
                "tags": ["Stock / Items"],
                "summary": "Adjust stock quantity",
                "parameters": [{"name": "variant_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {"content": {"application/json": {"schema": AdjustStockRequest.model_json_schema()}}},
                "responses": {
                    "200": {
                        "description": "Stock adjusted successfully",
                        "content": {"application/json": {"schema": StockItemOutSchema.model_json_schema()}}
                    },
                    **auth_errors,
                    **not_found,
                    **validation_errors
                },
            }
        }
    )

    spec.path(
        path="/api/v1/stock/items/{variant_id}/reserve",
        operations={
            "post": {
                "tags": ["Stock / Items"],
                "summary": "Reserve stock",
                "parameters": [{"name": "variant_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {"content": {"application/json": {"schema": ReserveStockRequest.model_json_schema()}}},
                "responses": {
                    "200": {
                        "description": "Stock reserved successfully",
                        "content": {"application/json": {"schema": StockItemOutSchema.model_json_schema()}}
                    },
                    **auth_errors,
                    **not_found,
                    **validation_errors
                },
            }
        }
    )

    spec.path(
        path="/api/v1/stock/items/{variant_id}/release",
        operations={
            "post": {
                "tags": ["Stock / Items"],
                "summary": "Release reserved stock",
                "parameters": [{"name": "variant_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {"content": {"application/json": {"schema": ReserveStockRequest.model_json_schema()}}},
                "responses": {
                    "200": {
                        "description": "Stock released successfully",
                        "content": {"application/json": {"schema": StockItemOutSchema.model_json_schema()}}
                    },
                    **auth_errors,
                    **not_found,
                    **validation_errors
                },
            }
        }
    )

    spec.path(
        path="/api/v1/stock/items/{variant_id}/ship",
        operations={
            "post": {
                "tags": ["Stock / Items"],
                "summary": "Ship reserved stock",
                "parameters": [{"name": "variant_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {"content": {"application/json": {"schema": ReserveStockRequest.model_json_schema()}}},
                "responses": {
                    "200": {
                        "description": "Stock shipped successfully",
                        "content": {"application/json": {"schema": StockItemOutSchema.model_json_schema()}}
                    },
                    **auth_errors,
                    **not_found,
                    **validation_errors
                },
            }
        }
    )

    spec.path(
        path="/api/v1/stock/items/{variant_id}/threshold",
        operations={
            "put": {
                "tags": ["Stock / Items"],
                "summary": "Set low stock threshold",
                "parameters": [{"name": "variant_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {"content": {"application/json": {"schema": SetLowStockThresholdRequest.model_json_schema()}}},
                "responses": {
                    "200": {
                        "description": "Low stock threshold updated",
                        "content": {"application/json": {"schema": StockItemOutSchema.model_json_schema()}}
                    },
                    **auth_errors,
                    **not_found,
                    **validation_errors
                },
            }
        }
    )
