from __future__ import annotations

from typing import Callable
from src.core.repositories.base_uow import BaseUnitOfWork
from src.core.events.dispatcher import EventDispatcher
from src.app.domain_service import DomainService
import redis

from src.domains.accounts.services import AccountDomainService
from src.domains.auth.services.auth import AuthService
from src.domains.auth.repositories.redis_denylist import RedisDenylistRepository
from src.domains.rbac.services import RbacDomainService
from src.domains.catalog.services import CatalogDomainService
from src.domains.stock.services import StockDomainService
from src.domains.stock.services.stock_item_service import StockItemService
from src.domains.stock.services.stock_movement_service import StockMovementService
from src.domains.sale.services import SaleDomainService, SaleService, RefundService
from src.domains.billing.services import BillingDomainService
from src.domains.billing.services.payment_service import PaymentService
from src.domains.billing.services.payment_method_service import PaymentMethodService
from src.core.services.storage import LocalDiskStorage


def build_domain_service(
    uow_factory: Callable[[], BaseUnitOfWork],
    redis_client: redis.Redis[str],
    dispatcher: EventDispatcher,
    upload_folder: str = "uploads",
) -> DomainService:
    return DomainService(
        accounts=AccountDomainService(uow_factory),
        auth=AuthService(uow_factory, RedisDenylistRepository(redis_client), dispatcher),
        rbac=RbacDomainService(uow_factory),
        catalog=CatalogDomainService(uow_factory, LocalDiskStorage(upload_folder)),
        stock=StockDomainService(
            item=StockItemService(uow_factory),
            movement=StockMovementService(uow_factory),
        ),
        sale=SaleDomainService(
            sale=SaleService(uow_factory),
            refund=RefundService(uow_factory),
        ),
        billing=BillingDomainService(
            payment=PaymentService(uow_factory),
            payment_method=PaymentMethodService(uow_factory),
        ),
    )
