"""SQL implementations of the accounts repositories."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from src.domains.accounts.entities import Account, AccountRole, Credential
from src.domains.accounts.repositories.base_repository import (
    AccountFilter,
    BaseAccountRepository,
    BaseAccountRoleRepository,
    BaseCredentialRepository,
)
from src.domains.accounts.repositories.sql.models import (
    AccountModel,
    AccountRoleModel,
    CredentialModel,
)
from src.domains.accounts.repositories.utils.mappers import (
    account_role_to_entity,
    account_role_to_model,
    account_to_entity,
    account_to_model,
    credential_to_entity,
    credential_to_model,
)
from src.domains.shared.filters import BaseFilter
from src.domains.shared.pagination import Paginated, PaginationMeta


class SqlAccountRepository(BaseAccountRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entity: Account) -> Account:
        model = account_to_model(entity)
        self._session.add(model)
        self._session.flush()
        return entity

    def get(self, entity_id: UUID) -> Account | None:
        model = self._session.get(AccountModel, entity_id)
        return account_to_entity(model) if model else None

    def list(self, filters: AccountFilter) -> Paginated[Account]:
        query = select(AccountModel)
        query = self._apply_filter(query, filters)
        total = self._session.scalar(
            select(AccountModel).where(
                *([AccountModel.status == filters.status] if filters.status else []),
            ).with_only_columns(AccountModel.id)
        )
        # total count
        from sqlalchemy import func
        count_q = select(func.count()).select_from(AccountModel)
        if filters.status:
            count_q = count_q.where(AccountModel.status == filters.status)
        if filters.search:
            search = f"%{filters.search}%"
            count_q = count_q.where(
                or_(
                    AccountModel.first_name.ilike(search),
                    AccountModel.last_name.ilike(search),
                )
            )
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
        return q.order_by(AccountModel.created_at.desc())

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


class SqlCredentialRepository(BaseCredentialRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entity: Credential) -> Credential:
        model = credential_to_model(entity)
        self._session.add(model)
        self._session.flush()
        return entity

    def get(self, entity_id: UUID) -> Credential | None:
        model = self._session.get(CredentialModel, entity_id)
        return credential_to_entity(model) if model else None

    def get_by_account(self, account_id: UUID) -> Credential | None:
        model = self._session.scalar(
            select(CredentialModel).where(CredentialModel.account_id == account_id)
        )
        return credential_to_entity(model) if model else None

    def get_by_username(self, username: str) -> Credential | None:
        model = self._session.scalar(
            select(CredentialModel).where(CredentialModel.username == username)
        )
        return credential_to_entity(model) if model else None

    def get_by_email(self, email: str) -> Credential | None:
        model = self._session.scalar(
            select(CredentialModel).where(CredentialModel.email == email)
        )
        return credential_to_entity(model) if model else None

    def get_by_username_or_email(self, value: str) -> Credential | None:
        model = self._session.scalar(
            select(CredentialModel).where(
                or_(CredentialModel.username == value, CredentialModel.email == value)
            )
        )
        return credential_to_entity(model) if model else None

    def list(self, filters: BaseFilter) -> Paginated[Credential]:
        from sqlalchemy import func
        total = self._session.scalar(select(func.count()).select_from(CredentialModel)) or 0
        models = self._session.scalars(
            select(CredentialModel).offset(filters.offset).limit(filters.limit)
        ).all()
        return Paginated(
            items=[credential_to_entity(m) for m in models],
            meta=PaginationMeta(page=filters.page, limit=filters.limit, total=total),
        )

    def _apply_filter(self, query: object, filters: BaseFilter) -> object:
        return query

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


class SqlAccountRoleRepository(BaseAccountRoleRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entity: AccountRole) -> AccountRole:
        model = account_role_to_model(entity)
        self._session.add(model)
        self._session.flush()
        return entity

    def get(self, account_id: UUID, role_id: UUID) -> AccountRole | None:
        model = self._session.scalar(
            select(AccountRoleModel).where(
                AccountRoleModel.account_id == account_id,
                AccountRoleModel.role_id == role_id,
            )
        )
        return account_role_to_entity(model) if model else None

    def list_by_account(self, account_id: UUID) -> list[AccountRole]:
        models = self._session.scalars(
            select(AccountRoleModel).where(AccountRoleModel.account_id == account_id)
        ).all()
        return [account_role_to_entity(m) for m in models]

    def list(self, filters: BaseFilter) -> Paginated[AccountRole]:
        from sqlalchemy import func
        total = self._session.scalar(
            select(func.count()).select_from(AccountRoleModel)
        ) or 0
        models = self._session.scalars(
            select(AccountRoleModel).offset(filters.offset).limit(filters.limit)
        ).all()
        return Paginated(
            items=[account_role_to_entity(m) for m in models],
            meta=PaginationMeta(page=filters.page, limit=filters.limit, total=total),
        )

    def _apply_filter(self, query: object, filters: BaseFilter) -> object:
        return query

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
