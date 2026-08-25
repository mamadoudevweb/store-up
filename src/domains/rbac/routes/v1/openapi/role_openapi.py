from src.core.docs.openapi_registry import spec
from src.domains.rbac.routes.v1.schemas.rbac_schemas import (
    RoleResponse,
    CreateRoleRequest,
    UpdateRoleRequest,
)

def register_role_docs() -> None:
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
        path="/api/v1/roles",
        operations={
            "get": {
                "tags": ["RBAC / Roles"],
                "summary": "List roles",
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}},
                    {"name": "name", "in": "query", "schema": {"type": "string"}},
                ],
                "responses": {
                    "200": {"description": "Paginated list of roles"},
                    **auth_errors
                },
            },
            "post": {
                "tags": ["RBAC / Roles"],
                "summary": "Create role",
                "requestBody": {"required": True, "content": {"application/json": {"schema": CreateRoleRequest.model_json_schema()}}},
                "responses": {
                    "201": {
                        "description": "Role created successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "data": RoleResponse.model_json_schema()
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
        path="/api/v1/roles/{role_id}",
        operations={
            "get": {
                "tags": ["RBAC / Roles"],
                "summary": "Get role by ID",
                "parameters": [{"name": "role_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {
                        "description": "Role details",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "data": RoleResponse.model_json_schema()
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
                "tags": ["RBAC / Roles"],
                "summary": "Delete role",
                "parameters": [{"name": "role_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"description": "Role deleted successfully"},
                    **auth_errors,
                    **not_found
                },
            }
        }
    )
