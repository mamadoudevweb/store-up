"""SQL implementation of AccountRole repository."""
from __future__ import annotations
from typing import Any

from src.core.repositories.sql.base_sql_repository import BaseSqlRepository
from src.domains.accounts.entities import AccountRole
from src.domains.accounts.repositories.filters import AccountRoleFilter
from src.domains.accounts.repositories.sql.orms import AccountRoleModel
from src.domains.accounts.repositories.utils import AccountRoleMapper

class SqlAccountRoleRepository(BaseSqlRepository[AccountRole, AccountRoleFilter]):
    model = AccountRoleModel
    mapper = AccountRoleMapper()
    filter_cls = AccountRoleFilter

    def _apply_filter(self, query: Any, entity_filter: AccountRoleFilter) -> Any:
        q = query
        if entity_filter.account_id:
            q = q.where(AccountRoleModel.account_id == entity_filter.account_id)
        if entity_filter.role_id:
            q = q.where(AccountRoleModel.role_id == entity_filter.role_id)
        return q

    def update(self, entity: AccountRole) -> AccountRole:
        # AccountRole doesn't have an `id` field. Since it's mainly mapping keys, we can just return it.
        return entity

    def delete(self, entity: AccountRole) -> None:
        model = self._session.get(self.model, (entity.account_id, entity.role_id))
        if model:
            self._session.delete(model)
            self._session.flush()
