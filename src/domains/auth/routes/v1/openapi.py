from src.core.docs.openapi_registry import spec

def register() -> None:
    spec.path(
        path="/api/v1/auth/login",
        operations={
            "post": {
                "summary": "Login to get access and refresh tokens",
                "responses": {
                    "200": {
                        "description": "Tokens generated successfully",
                    }
                }
            }
        }
    )
    spec.path(
        path="/api/v1/auth/logout",
        operations={
            "post": {
                "summary": "Logout to revoke the access token",
                "responses": {
                    "200": {
                        "description": "Logged out successfully",
                    }
                }
            }
        }
    )
    spec.path(
        path="/api/v1/auth/refresh",
        operations={
            "post": {
                "summary": "Refresh access token",
                "responses": {
                    "200": {
                        "description": "New access token generated successfully",
                    }
                }
            }
        }
    )
