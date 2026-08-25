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
# Catalog
from src.domains.catalog.repositories.sql.product_repository import SqlProductRepository
from src.domains.catalog.repositories.sql.product_variant_repository import SqlProductVariantRepository
from src.domains.catalog.repositories.sql.product_category_repository import SqlProductCategoryRepository
from src.domains.catalog.repositories.sql.brand_repository import SqlBrandRepository
from src.domains.catalog.repositories.sql.category_repository import SqlCategoryRepository
from src.domains.catalog.repositories.sql.product_image_repository import SqlProductImageRepository
from src.domains.catalog.repositories.sql.attribute_repository import SqlAttributeRepository, SqlAttributeValueRepository
# Stock
from src.domains.stock.repositories.sql.stock_item_repository import SqlStockItemRepository
from src.domains.stock.repositories.sql.stock_movement_repository import SqlStockMovementRepository
# Sale
from src.domains.sale.repositories.sql.sale_repository import SqlSaleRepository
from src.domains.sale.repositories.sql.refund_repository import SqlRefundRepository

REPOSITORY_CLASSES: dict[str, type[Any]] = {
    # Account domain
    "accounts": SqlAccountRepository,
    "credentials": SqlCredentialRepository,
    "account_roles": SqlAccountRoleRepository,

    # RBAC domain
    "roles": RbacSqlRoleRepository,
    "permissions": SqlPermissionRepository,
    "role_permissions": SqlRolePermissionRepository,

    # Catalog domain
    "products": SqlProductRepository,
    "product_variants": SqlProductVariantRepository,
    "product_categories": SqlProductCategoryRepository,
    "brands": SqlBrandRepository,
    "categories": SqlCategoryRepository,
    "product_images": SqlProductImageRepository,
    "attributes": SqlAttributeRepository,
    "attribute_values": SqlAttributeValueRepository,

    # Stock domain
    "stock_items": SqlStockItemRepository,
    "stock_movements": SqlStockMovementRepository,
    
    # Sale domain
    "sales": SqlSaleRepository,
    "refunds": SqlRefundRepository,
}

def build_uow_factory(session_factory: Callable[[], Session], dispatcher: EventDispatcher) -> Callable[[], SqlUnitOfWork]:
    return lambda: SqlUnitOfWork(session_factory, dispatcher, REPOSITORY_CLASSES)
