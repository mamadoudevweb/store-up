"""Integration tests for AccountService."""
from __future__ import annotations

import pytest
import uuid

from src.domains.accounts.exceptions import (
    AccountNotFound,
    CredentialAlreadyExists,
    UsernameConflict,
)
from src.domains.accounts.repositories.sql.sql_uow import SqlAccountUnitOfWork
from src.domains.accounts.services import AccountService
from src.domains.shared.events import EventBus


@pytest.fixture
def account_service(uow_factory):
    # uow_factory provides the shared db_session
    uow = SqlAccountUnitOfWork(uow_factory)
    bus = EventBus()
    return AccountService(uow, bus)


def test_create_and_get_account(account_service):
    res = account_service.account.create_account("Charlie", "Chaplin")
    assert res.is_success
    account_id = res.data.id
    
    get_res = account_service.account.get_account(account_id)
    assert get_res.is_success
    assert get_res.data.first_name == "Charlie"


def test_set_credentials_conflicts(account_service):
    # Create account
    account_id = account_service.account.create_account("Dan", "Dare").data.id
    
    # Set credentials
    res = account_service.credential.set_credentials(
        account_id, "dan", "dan@example.com", "password123"
    )
    assert res.is_success
    
    # Try to set again for same account
    with pytest.raises(CredentialAlreadyExists):
        account_service.credential.set_credentials(
            account_id, "dan2", "dan2@example.com", "password123"
        )
        
    # Create second account
    account_id2 = account_service.account.create_account("Eve", "Evil").data.id
    
    # Try to use same username
    with pytest.raises(UsernameConflict):
        account_service.credential.set_credentials(
            account_id2, "dan", "eve@example.com", "password123"
        )
