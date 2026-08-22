"""Auth service logic."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID
from datetime import datetime, timezone
from typing import Callable

import bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token

from src.core.services.base_service import BaseService
from src.core.services.result import ServiceResult
from src.core.repositories.base_uow import BaseUnitOfWork
from src.core.events.dispatcher import EventDispatcher
from src.domains.accounts.repositories.filters import CredentialFilter
from src.domains.auth.events import UserLoggedIn, UserLoggedOut
from src.domains.auth.exceptions import InvalidCredentials
from src.domains.auth.repositories.base_denylist import DenylistRepository


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str


class AuthService(BaseService):
    """Business logic for authentication."""

    def __init__(
        self,
        uow_factory: Callable[[], BaseUnitOfWork],
        denylist: DenylistRepository,
        dispatcher: EventDispatcher,
    ) -> None:
        super().__init__(uow_factory)
        self._denylist = denylist
        self._dispatcher = dispatcher

    def login(self, username: str, password: str, ip_address: str | None = None) -> ServiceResult[TokenPair]:
        """Validates credentials and returns JWT tokens."""
        with self._uow_factory() as uow:
            cred = uow.credentials.get(CredentialFilter(username_or_email=username))
            if not cred:
                raise InvalidCredentials()

            # Verify password
            if not bcrypt.checkpw(password.encode(), cred.password_hash.encode()):
                raise InvalidCredentials()

            account = uow.accounts.get(cred.account_id)
            if not account or not account.is_active():
                raise InvalidCredentials("Account is inactive or suspended.")

            # Generate tokens
            # We use the account_id as the identity
            identity = str(account.id)
            access_token = create_access_token(identity=identity)
            refresh_token = create_refresh_token(identity=identity)

            # Update last login
            cred.last_login_at = datetime.now(timezone.utc)
            cred.register_event(
                UserLoggedIn(account_id=account.id, username=cred.username, ip_address=ip_address)
            )
            uow.credentials.update(cred)
            uow.track(cred)
            uow.commit()

        return ServiceResult(data=TokenPair(access_token, refresh_token))

    def logout(self, jti: str, exp: int) -> ServiceResult[None]:
        """Revokes an access token by placing it on the denylist."""
        self._denylist.add(jti, exp)
        self._dispatcher.dispatch(UserLoggedOut(jti=jti))
        return ServiceResult(data=None)

    def is_token_revoked(self, jti: str) -> bool:
        """Checks if a token has been revoked."""
        return self._denylist.is_revoked(jti)

    def refresh(self, identity: str) -> ServiceResult[str]:
        """Issues a new access token based on a refresh token's identity."""
        with self._uow_factory() as uow:
            account = uow.accounts.get(UUID(identity))
            if not account or not account.is_active():
                raise InvalidCredentials("Account is inactive or suspended.")
                
        access_token = create_access_token(identity=identity)
        return ServiceResult(data=access_token)
