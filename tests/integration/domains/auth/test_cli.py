"""Integration tests for Auth CLI commands."""
from __future__ import annotations

import pytest

from src.domains.accounts.repositories.sql.sql_uow import SqlAccountUnitOfWork
from src.domains.accounts.services import AccountService
from src.domains.accounts.repositories.filters import CredentialFilter
from src.domains.shared.events import EventBus


@pytest.fixture
def test_app(uow_factory):
    # To test CLI we need the app and test runner
    from src.app import create_app
    app = create_app("testing")
    
    # Wire the test UoW and EventBus explicitly for the test app
    uow = SqlAccountUnitOfWork(uow_factory)
    bus = EventBus()
    app.extensions["account_service"] = AccountService(uow, bus)
    # We mock out rbac_service since it's not implemented yet
    
    with app.app_context():
        yield app


def test_bootstrap_superuser_cli(test_app, uow_factory):
    runner = test_app.test_cli_runner()
    
    result = runner.invoke(test_app.cli.get_command(test_app.cli, "bootstrap-superuser"), [
        "--first-name", "Admin",
        "--last-name", "User",
        "--username", "superuser",
        "--email", "admin@store.com",
        "--password", "securepassword",
    ])
    
    assert result.exit_code == 0
    assert "Superuser 'superuser' created successfully!" in result.output
    
    # Verify via database
    uow = SqlAccountUnitOfWork(uow_factory)
    with uow:
        cred = uow.credentials.get(CredentialFilter(username_or_email="superuser"))
        assert cred is not None
        assert cred.email == "admin@store.com"
