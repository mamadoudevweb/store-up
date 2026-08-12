"""Accounts services package — AccountService aggregates sub-services via properties."""
from __future__ import annotations

from src.domains.accounts.repositories.base_uow import BaseAccountUnitOfWork
from src.domains.accounts.services import account as account_svc
from src.domains.accounts.services import account_role as role_svc
from src.domains.accounts.services import credential as credential_svc
from src.domains.shared.events import EventBus


class AccountService:
    """Facade aggregating operations on accounts, credentials, and roles."""

    def __init__(self, uow: BaseAccountUnitOfWork, event_bus: EventBus) -> None:
        self._account = account_svc.Service(uow, event_bus)
        self._credential = credential_svc.Service(uow, event_bus)
        self._role = role_svc.Service(uow, event_bus)

    @property
    def account(self) -> account_svc.Service:
        return self._account

    @property
    def credential(self) -> credential_svc.Service:
        return self._credential

    @property
    def role(self) -> role_svc.Service:
        return self._role
