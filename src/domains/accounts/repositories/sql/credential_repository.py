"""SQL implementation of Credential repository."""
from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from src.domains.accounts.entities import Credential
from src.domains.accounts.repositories.filters import CredentialFilter
from src.domains.accounts.repositories.sql.orms import CredentialModel
from src.domains.accounts.repositories.utils import credential_to_entity, credential_to_model
from src.domains.shared.pagination import Paginated, PaginationMeta
from src.domains.shared.repositories import BaseRepository


class SqlCredentialRepository(BaseRepository[Credential, CredentialFilter]):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entity: Credential) -> Credential:
        model = credential_to_model(entity)
        self._session.add(model)
        self._session.flush()
        return entity

    def get(self, filters: CredentialFilter) -> Credential | None:
        query = select(CredentialModel)
        query = self._apply_filter(query, filters)
        model = self._session.scalar(query.limit(1))
        return credential_to_entity(model) if model else None

    def exists(self, filters: CredentialFilter) -> bool:
        from sqlalchemy import exists
        query = select(CredentialModel)
        query = self._apply_filter(query, filters)
        stmt = select(exists(query.subquery()))
        return self._session.scalar(stmt) or False

    def list(self, filters: CredentialFilter) -> Paginated[Credential]:
        query = select(CredentialModel)
        query = self._apply_filter(query, filters)
        
        from sqlalchemy import func
        count_q = select(func.count()).select_from(CredentialModel)
        count_q = self._apply_filter(count_q, filters)
        total = self._session.scalar(count_q) or 0

        query = query.offset(filters.offset).limit(filters.limit)
        models = self._session.scalars(query).all()
        return Paginated(
            items=[credential_to_entity(m) for m in models],
            meta=PaginationMeta(page=filters.page, limit=filters.limit, total=total),
        )

    def _apply_filter(self, query: object, filters: CredentialFilter) -> object:
        from sqlalchemy import Select
        q: Select = query  # type: ignore[assignment]
        if filters.id:
            q = q.where(CredentialModel.id == filters.id)
        if filters.account_id:
            q = q.where(CredentialModel.account_id == filters.account_id)
        if filters.username:
            q = q.where(CredentialModel.username == filters.username)
        if filters.email:
            q = q.where(CredentialModel.email == filters.email)
        if filters.username_or_email:
            q = q.where(
                or_(
                    CredentialModel.username == filters.username_or_email,
                    CredentialModel.email == filters.username_or_email,
                )
            )
        return q

    def update(self, entity: Credential) -> Credential:
        model = self._session.get(CredentialModel, entity.id)
        if model:
            credential_to_model(entity, existing=model)
            self._session.flush()
        return entity

    def delete(self, entity: Credential) -> None:
        model = self._session.get(CredentialModel, entity.id)
        if model:
            self._session.delete(model)
            self._session.flush()
