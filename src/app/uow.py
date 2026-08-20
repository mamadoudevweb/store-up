from typing import Any, Callable
from sqlalchemy.orm import Session
from src.core.events.dispatcher import EventDispatcher
from src.core.repositories.sql.sql_uow import SqlUnitOfWork

# Import all concrete SQL repositories
# Accounts
from src.domains.accounts.repositories.sql.account_repository import SqlAccountRepository
from src.domains.accounts.repositories.sql.credential_repository import SqlCredentialRepository
from src.domains.accounts.repositories.sql.account_role_repository import SqlAccountRoleRepository
# RBAC
from src.domains.rbac.repositories.sql.role_repository import SqlRoleRepository as RbacSqlRoleRepository
from src.domains.rbac.repositories.sql.permission_repository import SqlPermissionRepository
from src.domains.rbac.repositories.sql.role_permission_repository import SqlRolePermissionRepository
# Products
from src.domains.products.repositories.sql.product_repository import SqlProductRepository
from src.domains.products.repositories.sql.brand_repository import SqlBrandRepository
from src.domains.products.repositories.sql.category_repository import SqlCategoryRepository
from src.domains.products.repositories.sql.product_image_repository import SqlProductImageRepository
# Inventory, Sales, Notifications, Reports etc. when implemented

REPOSITORY_CLASSES: dict[str, type[Any]] = {
    # Account domain
    "accounts": SqlAccountRepository,
    "credentials": SqlCredentialRepository,
    "account_roles": SqlAccountRoleRepository,
    
    # RBAC domain
    "roles": RbacSqlRoleRepository,
    "permissions": SqlPermissionRepository,
    "role_permissions": SqlRolePermissionRepository,
    
    # Products domain
    "products": SqlProductRepository,
    "brands": SqlBrandRepository,
    "categories": SqlCategoryRepository,
    "product_images": SqlProductImageRepository,
}

def build_uow_factory(session_factory: Callable[[], Session], dispatcher: EventDispatcher) -> Callable[[], SqlUnitOfWork]:
    return lambda: SqlUnitOfWork(session_factory, dispatcher, REPOSITORY_CLASSES)
