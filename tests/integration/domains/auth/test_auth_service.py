"""Integration tests for AuthService."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from src.domains.accounts.repositories.sql.sql_uow import SqlAccountUnitOfWork
from src.domains.accounts.services import AccountService
from src.domains.auth.repositories.memory_denylist import InMemoryTokenDenylist
from src.domains.auth.services import AuthService
from src.domains.auth.exceptions import InvalidCredentials
from src.domains.shared.events import EventBus

# Note: We need a Flask application context for flask_jwt_extended to generate tokens.
# Let's create a fixture for the Flask app.


@pytest.fixture
def test_app():
    from src.app import create_app
    app = create_app("testing")
    app.config["JWT_SECRET_KEY"] = "super-secret"
    with app.app_context():
        yield app


@pytest.fixture
def auth_components(uow_factory):
    uow = SqlAccountUnitOfWork(uow_factory)
    bus = EventBus()
    denylist = InMemoryTokenDenylist()
    
    # We also need the account service to setup test accounts
    account_service = AccountService(uow, bus)
    auth_service = AuthService(uow, denylist, bus)
    
    return account_service, auth_service


def test_auth_service_login_success(test_app, auth_components):
    account_service, auth_service = auth_components
    
    # 1. Setup
    account_id = account_service.account.create_account("Alice", "Wonderland").data.id
    account_service.credential.set_credentials(
        account_id, "alice", "alice@example.com", "password123"
    )
    
    # 2. Login
    res = auth_service.login("alice", "password123", "127.0.0.1")
    assert res.success
    assert res.data.access_token is not None
    assert res.data.refresh_token is not None


def test_auth_service_login_failure(test_app, auth_components):
    account_service, auth_service = auth_components
    
    # 1. Setup
    account_id = account_service.account.create_account("Bob", "Builder").data.id
    account_service.credential.set_credentials(
        account_id, "bob", "bob@example.com", "correcthorse"
    )
    
    # 2. Login with wrong password
    with pytest.raises(InvalidCredentials):
        auth_service.login("bob", "wrongpassword")
        
    # 3. Login with wrong username
    with pytest.raises(InvalidCredentials):
        auth_service.login("bobby", "correcthorse")


def test_auth_service_logout(test_app, auth_components):
    account_service, auth_service = auth_components
    
    account_id = account_service.account.create_account("Eve", "Hacker").data.id
    account_service.credential.set_credentials(
        account_id, "eve", "eve@example.com", "password123"
    )
    
    res = auth_service.login("eve", "password123")
    assert res.success
    
    # Normally we'd get jti/exp from the decoded token, but we can mock it here
    jti = "mock-jti"
    exp = int(datetime.now(timezone.utc).timestamp()) + 3600
    
    # Logout
    auth_service.logout(jti, exp)
    
    # Check denylist
    assert auth_service._denylist.is_revoked(jti)
