from src.core.docs.openapi_registry import spec
from src.domains.accounts.routes.v1.schemas.account_schemas import (
    AccountResponse,
    CreateAccountRequest,
)

def register() -> None:
    # We use apispec and apispec.ext.marshmallow, but pydantic schemas can be mapped manually or using another ext.
    # We will register paths for accounts.
    spec.path(
        path="/api/v1/accounts",
        operations={
            "get": {
                "summary": "List accounts",
                "responses": {
                    "200": {
                        "description": "Paginated list of accounts",
                    }
                }
            },
            "post": {
                "summary": "Create account",
                "responses": {
                    "201": {
                        "description": "Account created",
                    }
                }
            }
        }
    )
