from src.core.docs.openapi_registry import spec
from src.domains.accounts.routes.v1.schemas.account_schemas import (
    AccountResponse,
    CreateAccountRequest,
    UpdateAccountRequest,
)

def register_account_docs() -> None:
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
        path="/api/v1/accounts",
        operations={
            "get": {
                "tags": ["Accounts"],
                "summary": "List accounts",
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}},
                    {"name": "search", "in": "query", "schema": {"type": "string"}},
                    {"name": "status", "in": "query", "schema": {"type": "string", "enum": ["active", "suspended"]}},
                ],
                "responses": {
                    "200": {"description": "Paginated list of accounts"},
                    **auth_errors
                },
            },
            "post": {
                "tags": ["Accounts"],
                "summary": "Create account",
                "requestBody": {"content": {"application/json": {"schema": CreateAccountRequest.model_json_schema()}}},
                "responses": {
                    "201": {"content": {"application/json": {"schema": AccountResponse.model_json_schema()}}},
                    **validation_errors
                },
            }
        }
    )

    spec.path(
        path="/api/v1/accounts/{account_id}",
        operations={
            "get": {
                "tags": ["Accounts"],
                "summary": "Get account by ID",
                "parameters": [{"name": "account_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"content": {"application/json": {"schema": AccountResponse.model_json_schema()}}},
                    **auth_errors,
                    **not_found
                },
            },
            "put": {
                "tags": ["Accounts"],
                "summary": "Update account",
                "parameters": [{"name": "account_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {"content": {"application/json": {"schema": UpdateAccountRequest.model_json_schema()}}},
                "responses": {
                    "200": {"content": {"application/json": {"schema": AccountResponse.model_json_schema()}}},
                    **auth_errors,
                    **not_found,
                    **validation_errors
                },
            },
            "delete": {
                "tags": ["Accounts"],
                "summary": "Suspend account",
                "parameters": [{"name": "account_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"content": {"application/json": {"schema": AccountResponse.model_json_schema()}}},
                    **auth_errors,
                    **not_found
                },
            }
        }
    )
