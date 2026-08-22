from typing import TYPE_CHECKING, Any
from flask import Flask

if TYPE_CHECKING:
    from src.domains.catalog.services import CatalogDomainService
    from src.domains.inventory.services import InventoryDomainService
    from src.domains.rbac.services import RbacDomainService
    from src.domains.accounts.services import AccountDomainService
    from src.domains.auth.services.auth import AuthService

class DomainService:
    """Aggregates every domain's DomainService. core/ and this class don't
    know the domain names in advance — the composition root supplies them."""

    if TYPE_CHECKING:
        catalog: CatalogDomainService
        inventory: InventoryDomainService
        rbac: RbacDomainService
        accounts: AccountDomainService
        auth: AuthService

    def __init__(self, **domains: Any) -> None:
        self.__dict__.update(domains)

    def init_app(self, app: Flask) -> None:
        app.extensions["domain_service"] = self
