"""Integration tests for Auth domain service."""
from __future__ import annotations

import pytest

from src.domains.auth.services.auth import AuthService
from src.domains.auth.repositories.memory_denylist import InMemoryTokenDenylist
from src.domains.auth.exceptions import InvalidCredentials
from src.domains.accounts.services import AccountDomainService
from src.domains.accounts.services.account import Service as AccountService
from src.domains.accounts.services.credential import Service as CredentialService
from src.core.events.dispatcher import EventDispatcher


@pytest.fixture
def auth_service(uow_factory):
    """Provides the AuthService using the test UoW."""
    # Auth service needs the account domain to verify credentials
    # For integration testing we instantiate exactly what's needed
    
    dispatcher = EventDispatcher()
    denylist = InMemoryTokenDenylist()
    
    return AuthService(
        uow_factory=uow_factory,
        dispatcher=dispatcher,
        denylist=denylist,
    )


def test_auth_login_success(auth_service, uow_factory, mock_actor):
    # Setup test account
    accounts_service = AccountDomainService(
        account=AccountService(uow_factory),
        credential=CredentialService(uow_factory)
    )
    account_id = accounts_service.account.create_account("Alice", "Auth").data.id
    accounts_service.credential.set_credentials(
        account_id, "alice", "alice@example.com", "password123"
    )

    # Login via Auth Service
    res = auth_service.login("alice", "password123")
    assert res.success
    assert "access_token" in res.data
    assert "refresh_token" in res.data


def test_auth_login_invalid(auth_service, uow_factory, mock_actor):
    # Setup test account
    accounts_service = AccountDomainService(
        account=AccountService(uow_factory),
        credential=CredentialService(uow_factory)
    )
    account_id = accounts_service.account.create_account("Bob", "Auth").data.id
    accounts_service.credential.set_credentials(
        account_id, "bob", "bob@example.com", "password123"
    )

    # Login via Auth Service with wrong password
    with pytest.raises(InvalidCredentials):
        auth_service.login("bob", "wrongpass")

    # Login with non-existent username
    with pytest.raises(InvalidCredentials):
        auth_service.login("nobody", "password123")


def test_auth_logout(auth_service):
    # Logout just puts JTI on denylist
    res = auth_service.logout("jti-12345", 9999999999)
    assert res.success
    
    # Check denylist
    assert auth_service._denylist.is_revoked("jti-12345")
