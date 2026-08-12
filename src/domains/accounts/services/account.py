"""Account entity service."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from src.domains.accounts.entities import Account
from src.domains.accounts.exceptions import AccountNotFound
from src.domains.accounts.repositories.filters import AccountFilter
from src.domains.accounts.repositories.base_uow import BaseAccountUnitOfWork
from src.domains.shared.events import EventBus
from src.domains.shared.pagination import Paginated
from src.domains.shared.service_result import ServiceResult


class Service:
    def __init__(self, uow: BaseAccountUnitOfWork, event_bus: EventBus) -> None:
        self._uow = uow
        self._bus = event_bus

    def create_account(
        self,
        first_name: str,
        last_name: str,
        birth_date: date | None = None,
    ) -> ServiceResult[Account]:
        account = Account.create(first_name, last_name, birth_date)
        with self._uow as uow:
            uow.accounts.add(account)
            uow.commit()
        self._bus.publish_all(account.pull_events())
        return ServiceResult.ok(account)

    def get_account(self, account_id: UUID) -> ServiceResult[Account]:
        with self._uow as uow:
            account = uow.accounts.get(AccountFilter(id=account_id))
        if not account:
            raise AccountNotFound()
        return ServiceResult.ok(account)

    def list_accounts(self, filters: AccountFilter) -> ServiceResult[Paginated[Account]]:
        with self._uow as uow:
            result = uow.accounts.list(filters)
        return ServiceResult.ok(result)

    def update_account(
        self,
        account_id: UUID,
        first_name: str | None = None,
        last_name: str | None = None,
        birth_date: date | None = None,
    ) -> ServiceResult[Account]:
        with self._uow as uow:
            account = uow.accounts.get(AccountFilter(id=account_id))
            if not account:
                raise AccountNotFound()
            account.update(first_name, last_name, birth_date)
            uow.accounts.update(account)
            uow.commit()
        self._bus.publish_all(account.pull_events())
        return ServiceResult.ok(account)

    def suspend_account(self, account_id: UUID) -> ServiceResult[Account]:
        with self._uow as uow:
            account = uow.accounts.get(AccountFilter(id=account_id))
            if not account:
                raise AccountNotFound()
            account.suspend()
            uow.accounts.update(account)
            uow.commit()
        self._bus.publish_all(account.pull_events())
        return ServiceResult.ok(account)
