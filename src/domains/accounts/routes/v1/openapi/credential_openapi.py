from src.core.docs.openapi_registry import spec
from src.domains.accounts.routes.v1.schemas.account_schemas import (
    CredentialResponse,
    SetCredentialsRequest,
    UpdateCredentialsRequest,
)

def register_credential_docs() -> None:
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
        path="/api/v1/accounts/{account_id}/credentials",
        operations={
            "get": {
                "tags": ["Accounts / Credentials"],
                "summary": "Get credentials",
                "parameters": [{"name": "account_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"content": {"application/json": {"schema": CredentialResponse.model_json_schema()}}},
                    **auth_errors,
                    **not_found
                },
            },
            "post": {
                "tags": ["Accounts / Credentials"],
                "summary": "Set initial credentials",
                "parameters": [{"name": "account_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {"content": {"application/json": {"schema": SetCredentialsRequest.model_json_schema()}}},
                "responses": {
                    "201": {"content": {"application/json": {"schema": CredentialResponse.model_json_schema()}}},
                    **validation_errors,
                    **not_found
                },
            },
            "put": {
                "tags": ["Accounts / Credentials"],
                "summary": "Update credentials",
                "parameters": [{"name": "account_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {"content": {"application/json": {"schema": UpdateCredentialsRequest.model_json_schema()}}},
                "responses": {
                    "200": {"content": {"application/json": {"schema": CredentialResponse.model_json_schema()}}},
                    **auth_errors,
                    **validation_errors,
                    **not_found
                },
            }
        }
    )
