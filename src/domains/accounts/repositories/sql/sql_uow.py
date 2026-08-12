"""SQL Unit of Work for the accounts domain."""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.domains.accounts.repositories.base_uow import BaseAccountUnitOfWork
from src.domains.accounts.repositories.sql.account_repository import SqlAccountRepository
from src.domains.accounts.repositories.sql.account_role_repository import SqlAccountRoleRepository
from src.domains.accounts.repositories.sql.credential_repository import SqlCredentialRepository


class SqlAccountUnitOfWork(BaseAccountUnitOfWork):
    """Owns the SQLAlchemy session for the accounts domain."""

    def __init__(self, session_factory: object) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None

    def __enter__(self) -> "SqlAccountUnitOfWork":
        self._session = self._session_factory()  # type: ignore[operator]
        self.accounts = SqlAccountRepository(self._session)
        self.credentials = SqlCredentialRepository(self._session)
        self.account_roles = SqlAccountRoleRepository(self._session)
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        if exc_type:
            self.rollback()
        self._session.close()  # type: ignore[union-attr]
        self._session = None

    def commit(self) -> None:
        self._session.commit()  # type: ignore[union-attr]

    def rollback(self) -> None:
        self._session.rollback()  # type: ignore[union-attr]
