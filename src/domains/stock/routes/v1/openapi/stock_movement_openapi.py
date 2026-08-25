from src.core.docs.openapi_registry import spec
from src.domains.stock.routes.v1.schemas.stock_schemas import StockMovementOutSchema

def register_stock_movement_docs() -> None:
    auth_errors = {
        "401": {"description": "Unauthorized"},
        "403": {"description": "Forbidden"}
    }
    not_found = {
        "404": {"description": "Not Found"}
    }

    spec.path(
        path="/api/v1/stock/movements",
        operations={
            "get": {
                "tags": ["Stock / Movements"],
                "summary": "List stock movements",
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}},
                    {"name": "stock_item_id", "in": "query", "schema": {"type": "string", "format": "uuid"}},
                    {"name": "reason", "in": "query", "schema": {"type": "string"}},
                    {"name": "reference_type", "in": "query", "schema": {"type": "string"}},
                    {"name": "reference_id", "in": "query", "schema": {"type": "string"}},
                    {"name": "sort", "in": "query", "schema": {"type": "string"}},
                    {"name": "order", "in": "query", "schema": {"type": "string", "enum": ["asc", "desc"], "default": "desc"}},
                ],
                "responses": {
                    "200": {"description": "Paginated list of stock movements"},
                    **auth_errors
                },
            }
        }
    )

    spec.path(
        path="/api/v1/stock/movements/{movement_id}",
        operations={
            "get": {
                "tags": ["Stock / Movements"],
                "summary": "Get stock movement by ID",
                "parameters": [{"name": "movement_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {
                        "description": "Stock movement details",
                        "content": {"application/json": {"schema": StockMovementOutSchema.model_json_schema()}}
                    },
                    **auth_errors,
                    **not_found
                },
            }
        }
    )
