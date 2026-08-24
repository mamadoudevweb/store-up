from src.core.docs.openapi_registry import spec
from src.domains.sale.routes.v1.schemas.sale_schemas import (
    CheckoutRequest, SaleResponse
)

def register() -> None:
    """Register sales checkout, completion, and failure endpoints in the OpenAPI specification."""
    spec.path(
        path="/api/v1/sales/checkout",
        operations={
            "post": {
                "tags": ["Sales"],
                "summary": "Checkout a sale",
                "requestBody": {"content": {"application/json": {"schema": CheckoutRequest.model_json_schema()}}},
                "responses": {
                    "201": {"content": {"application/json": {"schema": SaleResponse.model_json_schema()}}, "description": "Sale checked out"},
                    "422": {"description": "Validation error"},
                },
            }
        },
    )
    
    spec.path(
        path="/api/v1/sales/{sale_id}/complete",
        operations={
            "post": {
                "tags": ["Sales"],
                "summary": "Complete a sale",
                "parameters": [
                    {"name": "sale_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}},
                ],
                "responses": {
                    "200": {"content": {"application/json": {"schema": SaleResponse.model_json_schema()}}, "description": "Sale completed"},
                },
            }
        },
    )

    spec.path(
        path="/api/v1/sales/{sale_id}/fail",
        operations={
            "post": {
                "tags": ["Sales"],
                "summary": "Fail a sale",
                "parameters": [
                    {"name": "sale_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}},
                ],
                "responses": {
                    "200": {"content": {"application/json": {"schema": SaleResponse.model_json_schema()}}, "description": "Sale failed"},
                },
            }
        },
    )
