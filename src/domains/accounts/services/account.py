"""Account entity service."""
from __future__ import annotations

from datetime import date
from uuid import UUID
from typing import Callable

from src.core.services.base_service import BaseService
from src.core.services.result import ServiceResult
from src.core.entities.pagination import Pagination
from src.core.repositories.base_uow import BaseUnitOfWork
from src.domains.accounts.entities import Account
from src.domains.accounts.exceptions import AccountNotFound
from src.domains.accounts.repositories.filters import AccountFilter


class Service(BaseService):
    def __init__(self, uow_factory: Callable[[], BaseUnitOfWork]) -> None:
        super().__init__(uow_factory)

    def create_account(
        self,
        first_name: str,
        last_name: str,
        birth_date: date | None = None,
    ) -> ServiceResult[Account]:
        account = Account.create(first_name, last_name, birth_date)
        with self._uow_factory() as uow:
            uow.accounts.add(account)
            uow.track(account)
            uow.commit()
        return ServiceResult(data=account)

    def get_account(self, account_id: UUID) -> ServiceResult[Account]:
        with self._uow_factory() as uow:
            account = uow.accounts.get(account_id) # by id
        if not account:
            raise AccountNotFound()
        return ServiceResult(data=account)

    def list_accounts(self, filters: AccountFilter) -> ServiceResult[Pagination[Account]]:
        with self._uow_factory() as uow:
            result = uow.accounts.list(filters)
        return ServiceResult(data=result)

    def update_account(
        self,
        account_id: UUID,
        first_name: str | None = None,
        last_name: str | None = None,
        birth_date: date | None = None,
    ) -> ServiceResult[Account]:
        with self._uow_factory() as uow:
            account = uow.accounts.get(account_id)
            if not account:
                raise AccountNotFound()
            account.update(first_name, last_name, birth_date)
            uow.accounts.update(account)
            uow.track(account)
            uow.commit()
        return ServiceResult(data=account)

    def suspend_account(self, account_id: UUID) -> ServiceResult[Account]:
        with self._uow_factory() as uow:
            account = uow.accounts.get(account_id)
            if not account:
                raise AccountNotFound()
            account.suspend()
            uow.accounts.update(account)
            uow.track(account)
            uow.commit()
        return ServiceResult(data=account)
