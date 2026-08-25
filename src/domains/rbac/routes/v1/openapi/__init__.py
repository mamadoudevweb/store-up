from src.domains.rbac.routes.v1.openapi.role_openapi import register_role_docs
from src.domains.rbac.routes.v1.openapi.permission_openapi import register_permission_docs
from src.domains.rbac.routes.v1.openapi.role_permission_openapi import register_role_permission_docs

def register() -> None:
    register_role_docs()
    register_permission_docs()
    register_role_permission_docs()
