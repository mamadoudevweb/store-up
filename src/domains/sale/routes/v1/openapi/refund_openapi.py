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
                "description": (
                    "Submits a refund request for a completed sale.\n\n"
                    "### Important Validation Rules\n"
                    "- The API safely aggregates all requested quantities by `sale_line_id`.\n"
                    "- Duplicate lines in the payload for the same `sale_line_id` will have their quantities summed up.\n"
                    "- If the total aggregated quantity for any line exceeds its available refundable quantity, the request is rejected with a `422 Validation Error`.\n"
                ),
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": RefundRequest.model_json_schema(),
                            "examples": {
                                "valid_request": {
                                    "summary": "Standard partial refund",
                                    "value": {
                                        "sale_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                        "processed_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                        "reason": "Customer returned item due to defect",
                                        "lines": [
                                            {
                                                "sale_line_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                                "quantity": 1
                                            }
                                        ]
                                    }
                                },
                                "duplicate_lines_handled": {
                                    "summary": "Duplicate lines are aggregated",
                                    "description": "If duplicate sale_line_ids are passed, their quantities are summed up (e.g. 2 + 1 = 3) and validated together against the limit.",
                                    "value": {
                                        "sale_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                        "processed_by": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                        "reason": "Accidental duplicate lines from frontend",
                                        "lines": [
                                            {
                                                "sale_line_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                                "quantity": 2
                                            },
                                            {
                                                "sale_line_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                                "quantity": 1
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {"content": {"application/json": {"schema": RefundResponse.model_json_schema()}}, "description": "Refund processed"},
                    "422": {"description": "Validation error"},
                },
            }
        },
    )
