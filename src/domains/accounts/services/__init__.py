"""Accounts services package — AccountDomainService aggregates sub-services via properties."""
from __future__ import annotations

from typing import Callable
from src.core.services.base_service import BaseService
from src.core.repositories.base_uow import BaseUnitOfWork
from src.domains.accounts.services import account as account_svc
from src.domains.accounts.services import account_role as role_svc
from src.domains.accounts.services import credential as credential_svc

class AccountDomainService(BaseService):
    """Facade aggregating operations on accounts, credentials, and roles."""

    def __init__(self, uow_factory: Callable[[], BaseUnitOfWork]) -> None:
        super().__init__(uow_factory)
        self._account = account_svc.Service(uow_factory)
        self._credential = credential_svc.Service(uow_factory)
        self._account_role = role_svc.Service(uow_factory)

    @property
    def account(self) -> account_svc.Service:
        return self._account

    @property
    def credential(self) -> credential_svc.Service:
        return self._credential

    @property
    def account_role(self) -> role_svc.Service:
        return self._account_role
