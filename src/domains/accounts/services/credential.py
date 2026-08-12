"""Credential entity service."""
from __future__ import annotations

from uuid import UUID

import bcrypt

from src.domains.accounts.entities import Credential
from src.domains.accounts.exceptions import (
    AccountNotFound,
    AccountSuspendedError,
    CredentialAlreadyExists,
    CredentialNotFound,
    EmailConflict,
    UsernameConflict,
)
from src.domains.accounts.repositories.filters import AccountFilter, CredentialFilter
from src.domains.accounts.repositories.base_uow import BaseAccountUnitOfWork
from src.domains.shared.events import EventBus
from src.domains.shared.service_result import ServiceResult


class Service:
    def __init__(self, uow: BaseAccountUnitOfWork, event_bus: EventBus) -> None:
        self._uow = uow
        self._bus = event_bus

    def set_credentials(
        self,
        account_id: UUID,
        username: str,
        email: str,
        password: str,
    ) -> ServiceResult[Credential]:
        with self._uow as uow:
            account = uow.accounts.get(AccountFilter(id=account_id))
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
            uow.commit()
        self._bus.publish_all(cred.pull_events())
        return ServiceResult.ok(cred)

    def get_credentials(self, account_id: UUID) -> ServiceResult[Credential]:
        with self._uow as uow:
            cred = uow.credentials.get(CredentialFilter(account_id=account_id))
        if not cred:
            raise CredentialNotFound()
        return ServiceResult.ok(cred)

    def update_credentials(
        self,
        account_id: UUID,
        username: str | None = None,
        email: str | None = None,
        password: str | None = None,
    ) -> ServiceResult[Credential]:
        with self._uow as uow:
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
            uow.commit()
        self._bus.publish_all(cred.pull_events())
        return ServiceResult.ok(cred)
