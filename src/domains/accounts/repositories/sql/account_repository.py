"""SQL implementation of Account repository."""
from __future__ import annotations
from typing import Any

from sqlalchemy import or_, select

from src.core.repositories.sql.base_sql_repository import BaseSqlRepository
from src.domains.accounts.entities import Account
from src.domains.accounts.repositories.filters import AccountFilter
from src.domains.accounts.repositories.sql.orms import AccountModel
from src.domains.accounts.repositories.utils import AccountMapper

class SqlAccountRepository(BaseSqlRepository[Account, AccountFilter]):
    model = AccountModel
    mapper = AccountMapper()
    filter_cls = AccountFilter

    def _apply_filter(self, query: Any, entity_filter: AccountFilter) -> Any:
        q = query
        if entity_filter.id:
            q = q.where(AccountModel.id == entity_filter.id)
        if entity_filter.status:
            q = q.where(AccountModel.status == entity_filter.status)
        if entity_filter.search:
            search = f"%{entity_filter.search}%"
            q = q.where(
                or_(
                    AccountModel.first_name.ilike(search),
                    AccountModel.last_name.ilike(search),
                )
            )
        return q
