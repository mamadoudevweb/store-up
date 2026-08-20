from abc import ABC
from typing import Callable, Protocol
from src.core.services.errors import PermissionDeniedError
from src.core.repositories.base_uow import BaseUnitOfWork

class SupportsPermissionCheck(Protocol):
    """The only thing a service needs from whatever 'account' object the
    route passes in. Defined here, in core, as a Protocol rather than a
    concrete Account import — core still doesn't depend on the Account
    domain, it only requires this one method to exist."""
    def has_permission(self, domain: str, entity: str, action: str) -> bool: ...

class BaseService(ABC):
    def __init__(self, uow_factory: Callable[[], BaseUnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def _authorize(self, account: SupportsPermissionCheck, domain: str, entity: str, action: str) -> None:
        if not account.has_permission(domain, entity, action):
            raise PermissionDeniedError(domain=domain, entity=entity, action=action)
