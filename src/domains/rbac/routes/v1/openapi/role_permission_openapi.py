from src.core.docs.openapi_registry import spec
from src.domains.rbac.routes.v1.schemas.rbac_schemas import AssignPermissionRequest

def register_role_permission_docs() -> None:
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
        path="/api/v1/roles/{role_id}/permissions",
        operations={
            "get": {
                "tags": ["RBAC / Roles"],
                "summary": "List permissions for a role",
                "parameters": [{"name": "role_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {
                    "200": {"description": "Paginated list of permissions assigned to the role"},
                    **auth_errors,
                    **not_found
                },
            },
            "post": {
                "tags": ["RBAC / Roles"],
                "summary": "Assign permission to role",
                "parameters": [{"name": "role_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {"required": True, "content": {"application/json": {"schema": AssignPermissionRequest.model_json_schema()}}},
                "responses": {
                    "201": {"description": "Permission assigned successfully"},
                    **auth_errors,
                    **not_found,
                    **validation_errors
                },
            }
        }
    )

    spec.path(
        path="/api/v1/roles/{role_id}/permissions/{permission_id}",
        operations={
            "delete": {
                "tags": ["RBAC / Roles"],
                "summary": "Revoke permission from role",
                "parameters": [
                    {"name": "role_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}},
                    {"name": "permission_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}
                ],
                "responses": {
                    "200": {"description": "Permission revoked successfully"},
                    **auth_errors,
                    **not_found
                },
            }
        }
    )
