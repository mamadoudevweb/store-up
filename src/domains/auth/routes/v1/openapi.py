from src.core.docs.openapi_registry import spec
from src.domains.auth.routes.v1.schemas.auth_schemas import LoginRequest, TokenResponse

def register() -> None:
    auth_errors = {
        "401": {"description": "Unauthorized"},
        "403": {"description": "Forbidden"}
    }
    validation_errors = {
        "400": {"description": "Bad Request"},
        "422": {"description": "Validation Error"}
    }

    spec.path(
        path="/api/v1/auth/login",
        operations={
            "post": {
                "tags": ["Auth"],
                "summary": "Login to get access and refresh tokens",
                "requestBody": {"required": True, "content": {"application/json": {"schema": LoginRequest.model_json_schema()}}},
                "responses": {
                    "200": {
                        "description": "Tokens generated successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "data": TokenResponse.model_json_schema()
                                    }
                                }
                            }
                        }
                    },
                    **auth_errors,
                    **validation_errors
                }
            }
        }
    )
    spec.path(
        path="/api/v1/auth/logout",
        operations={
            "post": {
                "tags": ["Auth"],
                "summary": "Logout to revoke the access token",
                "responses": {
                    "200": {
                        "description": "Logged out successfully",
                    },
                    **auth_errors
                }
            }
        }
    )
    spec.path(
        path="/api/v1/auth/refresh",
        operations={
            "post": {
                "tags": ["Auth"],
                "summary": "Refresh access token",
                "responses": {
                    "200": {
                        "description": "New access token generated successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "data": TokenResponse.model_json_schema()
                                    }
                                }
                            }
                        }
                    },
                    **auth_errors
                }
            }
        }
    )
