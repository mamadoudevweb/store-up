from src.core.docs.openapi_registry import spec
from src.domains.accounts.routes.v1.schemas.account_schemas import (
    AccountRoleResponse,
    AssignRoleRequest,
)

def register_account_role_docs() -> None:
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
        path="/api/v1/accounts/{account_id}/roles",
        operations={
            "get": {
                "tags": ["Accounts / Roles"],
                "summary": "List account roles",
                "parameters": [{"name": "account_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"description": "List of roles assigned to the account"},
                    **auth_errors,
                    **not_found
                },
            },
            "post": {
                "tags": ["Accounts / Roles"],
                "summary": "Assign role to account",
                "parameters": [{"name": "account_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {"content": {"application/json": {"schema": AssignRoleRequest.model_json_schema()}}},
                "responses": {
                    "201": {"content": {"application/json": {"schema": AccountRoleResponse.model_json_schema()}}},
                    **auth_errors,
                    **validation_errors,
                    **not_found
                },
            }
        }
    )

    spec.path(
        path="/api/v1/accounts/{account_id}/roles/{role_id}",
        operations={
            "delete": {
                "tags": ["Accounts / Roles"],
                "summary": "Revoke role from account",
                "parameters": [
                    {"name": "account_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}},
                    {"name": "role_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}
                ],
                "responses": {
                    "200": {"description": "Role revoked successfully"},
                    **auth_errors,
                    **not_found
                },
            }
        }
    )
