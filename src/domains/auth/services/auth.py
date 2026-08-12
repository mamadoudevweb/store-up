"""Auth service logic."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID
from datetime import datetime, timezone

import bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token

from src.domains.accounts.repositories.base_uow import BaseAccountUnitOfWork
from src.domains.accounts.repositories.filters import CredentialFilter, AccountFilter
from src.domains.auth.events import UserLoggedIn, UserLoggedOut
from src.domains.auth.exceptions import InvalidCredentials
from src.domains.auth.repositories.base_denylist import BaseTokenDenylist
from src.domains.shared.events import EventBus
from src.domains.shared.service_result import ServiceResult


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str


class AuthService:
    def __init__(
        self,
        account_uow: BaseAccountUnitOfWork,
        denylist: BaseTokenDenylist,
        event_bus: EventBus,
    ) -> None:
        self._uow = account_uow
        self._denylist = denylist
        self._bus = event_bus

    def login(self, username: str, password: str, ip_address: str | None = None) -> ServiceResult[TokenPair]:
        """Validates credentials and returns JWT tokens."""
        with self._uow as uow:
            cred = uow.credentials.get(CredentialFilter(username_or_email=username))
            if not cred:
                raise InvalidCredentials()

            # Verify password
            if not bcrypt.checkpw(password.encode(), cred.password_hash.encode()):
                raise InvalidCredentials()

            account = uow.accounts.get(AccountFilter(id=cred.account_id))
            if not account or not account.is_active():
                raise InvalidCredentials("Account is inactive or suspended.")

            # Generate tokens
            # We use the account_id as the identity
            identity = str(account.id)
            access_token = create_access_token(identity=identity)
            refresh_token = create_refresh_token(identity=identity)

            # Update last login
            cred.last_login_at = datetime.now(timezone.utc)
            uow.credentials.update(cred)
            uow.commit()

        self._bus.publish(
            UserLoggedIn(account_id=account.id, username=cred.username, ip_address=ip_address)
        )
        return ServiceResult.ok(TokenPair(access_token, refresh_token))

    def logout(self, jti: str, exp: int) -> ServiceResult[None]:
        """Revokes an access token by placing it on the denylist."""
        self._denylist.add(jti, exp)
        self._bus.publish(UserLoggedOut(jti=jti))
        return ServiceResult.ok(None)

    def refresh(self, identity: str) -> ServiceResult[str]:
        """Issues a new access token based on a refresh token's identity."""
        with self._uow as uow:
            account = uow.accounts.get(AccountFilter(id=UUID(identity)))
            if not account or not account.is_active():
                raise InvalidCredentials("Account is inactive or suspended.")
                
        access_token = create_access_token(identity=identity)
        return ServiceResult.ok(access_token)
