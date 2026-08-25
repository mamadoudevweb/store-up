from src.core.docs.openapi_registry import spec
from src.domains.rbac.routes.v1.schemas.rbac_schemas import (
    PermissionResponse,
    CreatePermissionRequest,
)

def register_permission_docs() -> None:
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
        path="/api/v1/permissions",
        operations={
            "get": {
                "tags": ["RBAC / Permissions"],
                "summary": "List permissions",
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}},
                    {"name": "resource", "in": "query", "schema": {"type": "string"}},
                    {"name": "action", "in": "query", "schema": {"type": "string"}},
                ],
                "responses": {
                    "200": {"description": "Paginated list of permissions"},
                    **auth_errors
                },
            },
            "post": {
                "tags": ["RBAC / Permissions"],
                "summary": "Create permission",
                "requestBody": {"required": True, "content": {"application/json": {"schema": CreatePermissionRequest.model_json_schema()}}},
                "responses": {
                    "201": {
                        "description": "Permission created successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "data": PermissionResponse.model_json_schema()
                                    }
                                }
                            }
                        }
                    },
                    **auth_errors,
                    **validation_errors
                },
            }
        }
    )

    spec.path(
        path="/api/v1/permissions/{permission_id}",
        operations={
            "get": {
                "tags": ["RBAC / Permissions"],
                "summary": "Get permission by ID",
                "parameters": [{"name": "permission_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {
                        "description": "Permission details",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "data": PermissionResponse.model_json_schema()
                                    }
                                }
                            }
                        }
                    },
                    **auth_errors,
                    **not_found
                },
            },
            "delete": {
                "tags": ["RBAC / Permissions"],
                "summary": "Delete permission",
                "parameters": [{"name": "permission_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"description": "Permission deleted successfully"},
                    **auth_errors,
                    **not_found
                },
            }
        }
    )
