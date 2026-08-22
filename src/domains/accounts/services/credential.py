"""Credential entity service."""
from __future__ import annotations

from uuid import UUID
from typing import Callable
import bcrypt

from src.core.services.base_service import BaseService, SupportsPermissionCheck
from src.core.services.result import ServiceResult
from src.core.repositories.base_uow import BaseUnitOfWork
from src.domains.accounts.entities import Credential
from src.domains.accounts.exceptions import (
    AccountNotFound,
    AccountSuspendedError,
    CredentialAlreadyExists,
    CredentialNotFound,
    EmailConflict,
    UsernameConflict,
)
from src.domains.accounts.repositories.filters import CredentialFilter

class Service(BaseService):
    def __init__(self, uow_factory: Callable[[], BaseUnitOfWork]) -> None:
        super().__init__(uow_factory)

    def set_credentials(
        self,
        account_id: UUID,
        username: str,
        email: str,
        password: str,
    ) -> ServiceResult[Credential]:
        # Registration doesn't strictly need actor authorization if it's open
        with self._uow_factory() as uow:
            account = uow.accounts.get(account_id)
            if not account:
                raise AccountNotFound()
            if not account.is_active():
                raise AccountSuspendedError()
                
            if uow.credentials.exists(CredentialFilter(account_id=account_id)):
                raise CredentialAlreadyExists()
                
            if uow.credentials.exists(CredentialFilter(username=username)):
                raise UsernameConflict()
                
            if uow.credentials.exists(CredentialFilter(email=email)):
                raise EmailConflict()
                
            password_hash = bcrypt.hashpw(
                password.encode(), bcrypt.gensalt()
            ).decode()
            cred = Credential.create(account_id, username, email, password_hash)
            uow.credentials.add(cred)
            uow.track(cred)
            uow.commit()
        return ServiceResult(data=cred)

    def get_credentials(self, actor: SupportsPermissionCheck, account_id: UUID) -> ServiceResult[Credential]:
        self._authorize(actor, "accounts", "credential", "read")
        with self._uow_factory() as uow:
            cred = uow.credentials.get(CredentialFilter(account_id=account_id))
        if not cred:
            raise CredentialNotFound()
        return ServiceResult(data=cred)

    def update_credentials(
        self,
        actor: SupportsPermissionCheck,
        account_id: UUID,
        username: str | None = None,
        email: str | None = None,
        password: str | None = None,
    ) -> ServiceResult[Credential]:
        self._authorize(actor, "accounts", "credential", "update")
        with self._uow_factory() as uow:
            cred = uow.credentials.get(CredentialFilter(account_id=account_id))
            if not cred:
                raise CredentialNotFound()
            
            if username and username != cred.username:
                if uow.credentials.exists(CredentialFilter(username=username)):
                    raise UsernameConflict()
            if email and email != cred.email:
                if uow.credentials.exists(CredentialFilter(email=email)):
                    raise EmailConflict()
                    
            password_hash: str | None = None
            if password:
                password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            cred.update(username, email, password_hash)
            uow.credentials.update(cred)
            uow.track(cred)
            uow.commit()
        return ServiceResult(data=cred)
