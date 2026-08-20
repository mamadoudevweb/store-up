from src.core.docs.openapi_registry import spec

def register() -> None:
    spec.path(
        path="/api/v1/roles",
        operations={
            "post": {
                "summary": "Create a new role",
                "responses": {
                    "201": {
                        "description": "Role created successfully",
                    }
                }
            },
            "get": {
                "summary": "List roles",
                "responses": {
                    "200": {
                        "description": "Roles retrieved successfully",
                    }
                }
            }
        }
    )
    spec.path(
        path="/api/v1/roles/{role_id}",
        operations={
            "get": {
                "summary": "Get a role by ID",
                "responses": {
                    "200": {
                        "description": "Role retrieved successfully",
                    }
                }
            },
            "delete": {
                "summary": "Delete a role by ID",
                "responses": {
                    "200": {
                        "description": "Role deleted successfully",
                    }
                }
            }
        }
    )
    spec.path(
        path="/api/v1/permissions",
        operations={
            "post": {
                "summary": "Create a new permission",
                "responses": {
                    "201": {
                        "description": "Permission created successfully",
                    }
                }
            },
            "get": {
                "summary": "List permissions",
                "responses": {
                    "200": {
                        "description": "Permissions retrieved successfully",
                    }
                }
            }
        }
    )
    spec.path(
        path="/api/v1/permissions/{permission_id}",
        operations={
            "get": {
                "summary": "Get a permission by ID",
                "responses": {
                    "200": {
                        "description": "Permission retrieved successfully",
                    }
                }
            },
            "delete": {
                "summary": "Delete a permission by ID",
                "responses": {
                    "200": {
                        "description": "Permission deleted successfully",
                    }
                }
            }
        }
    )
    spec.path(
        path="/api/v1/roles/{role_id}/permissions",
        operations={
            "post": {
                "summary": "Assign a permission to a role",
                "responses": {
                    "201": {
                        "description": "Permission assigned successfully",
                    }
                }
            },
            "get": {
                "summary": "List permissions for a role",
                "responses": {
                    "200": {
                        "description": "Permissions retrieved successfully",
                    }
                }
            }
        }
    )
    spec.path(
        path="/api/v1/roles/{role_id}/permissions/{permission_id}",
        operations={
            "delete": {
                "summary": "Revoke a permission from a role",
                "responses": {
                    "200": {
                        "description": "Permission revoked successfully",
                    }
                }
            }
        }
    )
