from typing import Callable
from src.core.repositories.base_uow import BaseUnitOfWork
from src.core.events.dispatcher import EventDispatcher
from src.app.domain_service import DomainService
import redis

from src.domains.accounts.services import AccountDomainService
from src.domains.auth.services.auth import AuthService
from src.domains.auth.repositories.redis_denylist import RedisTokenDenylist
from src.domains.rbac.services import RbacDomainService
# from src.domains.products.services.product_domain_service import ProductDomainService

def build_domain_service(
    uow_factory: Callable[[], BaseUnitOfWork], 
    redis_client: redis.Redis,
    dispatcher: EventDispatcher,
) -> DomainService:
    return DomainService(
        accounts=AccountDomainService(uow_factory),
        auth=AuthService(uow_factory, RedisTokenDenylist(redis_client), dispatcher),
        rbac=RbacDomainService(uow_factory),
    )


