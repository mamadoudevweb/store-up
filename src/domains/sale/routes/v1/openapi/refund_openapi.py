from src.core.docs.openapi_registry import spec
from src.domains.sale.routes.v1.schemas.sale_schemas import (
    RefundRequest, RefundResponse
)

def register() -> None:
    spec.path(
        path="/api/v1/refunds",
        operations={
            "post": {
                "tags": ["Sales / Refunds"],
                "summary": "Process a refund",
                "requestBody": {"content": {"application/json": {"schema": RefundRequest.model_json_schema()}}},
                "responses": {
                    "201": {"content": {"application/json": {"schema": RefundResponse.model_json_schema()}}, "description": "Refund processed"},
                    "422": {"description": "Validation error"},
                },
            }
        },
    )
