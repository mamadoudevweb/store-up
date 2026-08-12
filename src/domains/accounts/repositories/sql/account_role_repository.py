"""SQL implementation of AccountRole repository."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domains.accounts.entities import AccountRole
from src.domains.accounts.repositories.filters import AccountRoleFilter
from src.domains.accounts.repositories.sql.orms import AccountRoleModel
from src.domains.accounts.repositories.utils import account_role_to_entity, account_role_to_model
from src.domains.shared.pagination import Paginated, PaginationMeta
from src.domains.shared.repositories import BaseRepository


class SqlAccountRoleRepository(BaseRepository[AccountRole, AccountRoleFilter]):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entity: AccountRole) -> AccountRole:
        model = account_role_to_model(entity)
        self._session.add(model)
        self._session.flush()
        return entity

    def get(self, filters: AccountRoleFilter) -> AccountRole | None:
        query = select(AccountRoleModel)
        query = self._apply_filter(query, filters)
        model = self._session.scalar(query.limit(1))
        return account_role_to_entity(model) if model else None

    def exists(self, filters: AccountRoleFilter) -> bool:
        from sqlalchemy import exists
        query = select(AccountRoleModel)
        query = self._apply_filter(query, filters)
        stmt = select(exists(query.subquery()))
        return self._session.scalar(stmt) or False

    def list(self, filters: AccountRoleFilter) -> Paginated[AccountRole]:
        query = select(AccountRoleModel)
        query = self._apply_filter(query, filters)
        
        from sqlalchemy import func
        count_q = select(func.count()).select_from(AccountRoleModel)
        count_q = self._apply_filter(count_q, filters)
        total = self._session.scalar(count_q) or 0

        query = query.offset(filters.offset).limit(filters.limit)
        models = self._session.scalars(query).all()
        return Paginated(
            items=[account_role_to_entity(m) for m in models],
            meta=PaginationMeta(page=filters.page, limit=filters.limit, total=total),
        )

    def _apply_filter(self, query: object, filters: AccountRoleFilter) -> object:
        from sqlalchemy import Select
        q: Select = query  # type: ignore[assignment]
        if filters.account_id:
            q = q.where(AccountRoleModel.account_id == filters.account_id)
        if filters.role_id:
            q = q.where(AccountRoleModel.role_id == filters.role_id)
        return q

    def update(self, entity: AccountRole) -> AccountRole:
        return entity  # composite PK — re-add if needed

    def delete(self, entity: AccountRole) -> None:
        model = self._session.scalar(
            select(AccountRoleModel).where(
                AccountRoleModel.account_id == entity.account_id,
                AccountRoleModel.role_id == entity.role_id,
            )
        )
        if model:
            self._session.delete(model)
            self._session.flush()
