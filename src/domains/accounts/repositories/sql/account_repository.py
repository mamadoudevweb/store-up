"""SQL implementation of Account repository."""
from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from src.domains.accounts.entities import Account
from src.domains.accounts.repositories.filters import AccountFilter
from src.domains.accounts.repositories.sql.orms import AccountModel
from src.domains.accounts.repositories.utils import account_to_entity, account_to_model
from src.domains.shared.pagination import Paginated, PaginationMeta
from src.domains.shared.repositories import BaseRepository


class SqlAccountRepository(BaseRepository[Account, AccountFilter]):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entity: Account) -> Account:
        model = account_to_model(entity)
        self._session.add(model)
        self._session.flush()
        return entity

    def get(self, filters: AccountFilter) -> Account | None:
        query = select(AccountModel)
        query = self._apply_filter(query, filters)
        model = self._session.scalar(query.limit(1))
        return account_to_entity(model) if model else None

    def exists(self, filters: AccountFilter) -> bool:
        from sqlalchemy import exists
        query = select(AccountModel)
        query = self._apply_filter(query, filters)
        stmt = select(exists(query.subquery()))
        return self._session.scalar(stmt) or False

    def list(self, filters: AccountFilter) -> Paginated[Account]:
        query = select(AccountModel)
        query = self._apply_filter(query, filters)
        
        from sqlalchemy import func
        count_q = select(func.count()).select_from(AccountModel)
        count_q = self._apply_filter(count_q, filters)
        total = self._session.scalar(count_q) or 0

        query = query.offset(filters.offset).limit(filters.limit)
        models = self._session.scalars(query).all()
        return Paginated(
            items=[account_to_entity(m) for m in models],
            meta=PaginationMeta(page=filters.page, limit=filters.limit, total=total),
        )

    def _apply_filter(self, query: object, filters: AccountFilter) -> object:
        from sqlalchemy import Select
        q: Select = query  # type: ignore[assignment]
        if filters.id:
            q = q.where(AccountModel.id == filters.id)
        if filters.status:
            q = q.where(AccountModel.status == filters.status)
        if filters.search:
            search = f"%{filters.search}%"
            q = q.where(
                or_(
                    AccountModel.first_name.ilike(search),
                    AccountModel.last_name.ilike(search),
                )
            )
        # only order_by if not a count query
        return q

    def update(self, entity: Account) -> Account:
        model = self._session.get(AccountModel, entity.id)
        if model:
            account_to_model(entity, existing=model)
            self._session.flush()
        return entity

    def delete(self, entity: Account) -> None:
        model = self._session.get(AccountModel, entity.id)
        if model:
            self._session.delete(model)
            self._session.flush()
