"""Integration tests for Account domain services."""
from __future__ import annotations

import pytest
from datetime import date
from uuid import UUID

from src.domains.accounts.exceptions import (
    AccountNotFound,
    CredentialAlreadyExists,
    UsernameConflict,
)
from src.domains.accounts.services import AccountDomainService
from src.domains.accounts.services.account import Service as AccountService
from src.domains.accounts.services.credential import Service as CredentialService
from src.domains.accounts.services.account_role import Service as AccountRoleService


@pytest.fixture
def accounts_service(uow_factory):
    """Provides the AccountDomainService using the test UoW."""
    return AccountDomainService(uow_factory)


def test_create_and_get_account(accounts_service, mock_actor):
    res = accounts_service.account.create_account("Charlie", "Chaplin", date(1980, 1, 1))
    assert res.success
    account_id = res.data.id
    
    get_res = accounts_service.account.get_account(mock_actor, account_id)
    assert get_res.success
    assert get_res.data.first_name == "Charlie"
    assert get_res.data.last_name == "Chaplin"


def test_set_credentials_conflicts(accounts_service, mock_actor):
    # Create account
    account_id = accounts_service.account.create_account("Dan", "Dare").data.id
    
    # Set credentials
    res = accounts_service.credential.set_credentials(
        account_id, "dan", "dan@example.com", "password123"
    )
    assert res.success
    
    # Try to set again for same account
    with pytest.raises(CredentialAlreadyExists):
        accounts_service.credential.set_credentials(
            account_id, "dan2", "dan2@example.com", "password123"
        )
        
    # Create second account
    account_id2 = accounts_service.account.create_account("Eve", "Evil").data.id
    
    # Try to use same username
    with pytest.raises(UsernameConflict):
        accounts_service.credential.set_credentials(
            account_id2, "dan", "eve@example.com", "password123"
        )


def test_assign_account_role(accounts_service, mock_actor, uow_factory):
    # Manually create a role in RBAC domain (bypassing service for simplicity in account tests)
    from src.domains.rbac.entities import Role
    role = Role(name="admin")
    with uow_factory() as uow:
        role = uow.roles.add(role)
        uow.commit()

    account_id = accounts_service.account.create_account("Admin", "User").data.id

    res = accounts_service.account_role.assign_role(mock_actor, account_id, role.id)
    assert res.success
    assert res.data.account_id == account_id
    assert res.data.role_id == role.id
