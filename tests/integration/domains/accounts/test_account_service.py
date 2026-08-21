"""Integration tests for Account domain services."""
from __future__ import annotations

import pytest
from datetime import date
from uuid import UUID

from src.domains.accounts.exceptions import (
    AccountNotFound,
    AccountSuspendedError,
    CredentialAlreadyExists,
    CredentialNotFound,
    EmailConflict,
    UsernameConflict,
    RoleAlreadyAssigned,
    RoleAssignmentNotFound,
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

def test_get_account_not_found(accounts_service, mock_actor):
    import uuid
    with pytest.raises(AccountNotFound):
        accounts_service.account.get_account(mock_actor, uuid.uuid4())

def test_list_accounts(accounts_service, mock_actor):
    accounts_service.account.create_account("List1", "User1")
    accounts_service.account.create_account("List2", "User2")
    
    from src.domains.accounts.repositories.filters import AccountFilter
    res = accounts_service.account.list_accounts(mock_actor, AccountFilter(limit=10, page=1))
    assert res.success
    assert len(res.data.items) >= 2
    assert res.data.total >= 2

def test_update_account(accounts_service, mock_actor):
    # Success
    account_id = accounts_service.account.create_account("Update", "User").data.id
    res = accounts_service.account.update_account(
        mock_actor, account_id, first_name="UpdatedName", last_name="UpdatedLast", birth_date=date(2000, 1, 1)
    )
    assert res.success
    assert res.data.first_name == "UpdatedName"
    assert res.data.last_name == "UpdatedLast"
    assert res.data.birth_date == date(2000, 1, 1)

    # Not found
    import uuid
    with pytest.raises(AccountNotFound):
        accounts_service.account.update_account(mock_actor, uuid.uuid4(), first_name="Foo")

def test_suspend_account(accounts_service, mock_actor):
    # Success
    account_id = accounts_service.account.create_account("Suspend", "User").data.id
    res = accounts_service.account.suspend_account(mock_actor, account_id)
    assert res.success
    assert res.data.is_active() is False

    # Not found
    import uuid
    with pytest.raises(AccountNotFound):
        accounts_service.account.suspend_account(mock_actor, uuid.uuid4())

def test_set_credentials_errors(accounts_service, mock_actor):
    import uuid
    # AccountNotFound
    with pytest.raises(AccountNotFound):
        accounts_service.credential.set_credentials(uuid.uuid4(), "user", "user@test.com", "pass")

    # AccountSuspendedError
    account_id = accounts_service.account.create_account("Suspended", "User").data.id
    accounts_service.account.suspend_account(mock_actor, account_id)
    with pytest.raises(AccountSuspendedError):
        accounts_service.credential.set_credentials(account_id, "susp", "susp@test.com", "pass")

    # EmailConflict
    account_id1 = accounts_service.account.create_account("A", "A").data.id
    accounts_service.credential.set_credentials(account_id1, "user1", "same@test.com", "pass")
    
    account_id2 = accounts_service.account.create_account("B", "B").data.id
    with pytest.raises(EmailConflict):
        accounts_service.credential.set_credentials(account_id2, "user2", "same@test.com", "pass")

def test_get_credentials(accounts_service, mock_actor):
    # Success
    account_id = accounts_service.account.create_account("GetCred", "User").data.id
    accounts_service.credential.set_credentials(account_id, "getcred", "getcred@test.com", "pass")
    res = accounts_service.credential.get_credentials(mock_actor, account_id)
    assert res.success
    assert res.data.username == "getcred"
    assert res.data.email == "getcred@test.com"

    # Not found
    import uuid
    with pytest.raises(CredentialNotFound):
        accounts_service.credential.get_credentials(mock_actor, uuid.uuid4())

def test_update_credentials(accounts_service, mock_actor):
    # Success
    account_id = accounts_service.account.create_account("UpdCred", "User").data.id
    accounts_service.credential.set_credentials(account_id, "updcred", "updcred@test.com", "pass")
    
    res = accounts_service.credential.update_credentials(
        mock_actor, account_id, username="updcred_new", email="updcred_new@test.com", password="newpass"
    )
    assert res.success
    assert res.data.username == "updcred_new"
    assert res.data.email == "updcred_new@test.com"

    # CredentialNotFound
    import uuid
    with pytest.raises(CredentialNotFound):
        accounts_service.credential.update_credentials(mock_actor, uuid.uuid4(), username="foo")

    # UsernameConflict & EmailConflict
    account_id2 = accounts_service.account.create_account("UpdCred2", "User").data.id
    accounts_service.credential.set_credentials(account_id2, "otheruser", "otheruser@test.com", "pass")
    
    with pytest.raises(UsernameConflict):
        accounts_service.credential.update_credentials(mock_actor, account_id, username="otheruser")

    with pytest.raises(EmailConflict):
        accounts_service.credential.update_credentials(mock_actor, account_id, email="otheruser@test.com")


def test_account_role_errors(accounts_service, mock_actor, uow_factory):
    import uuid
    from src.domains.rbac.entities import Role

    # assign_role: AccountNotFound
    with pytest.raises(AccountNotFound):
        accounts_service.account_role.assign_role(mock_actor, uuid.uuid4(), uuid.uuid4())

    # assign_role: RoleAlreadyAssigned
    account_id = accounts_service.account.create_account("RoleErrs", "User").data.id
    role = Role(name="admin2")
    with uow_factory() as uow:
        role = uow.roles.add(role)
        uow.commit()

    accounts_service.account_role.assign_role(mock_actor, account_id, role.id)
    with pytest.raises(RoleAlreadyAssigned):
        accounts_service.account_role.assign_role(mock_actor, account_id, role.id)

def test_list_roles(accounts_service, mock_actor, uow_factory):
    account_id = accounts_service.account.create_account("ListRole", "User").data.id
    from src.domains.rbac.entities import Role
    role = Role(name="editor")
    with uow_factory() as uow:
        role = uow.roles.add(role)
        uow.commit()
        
    accounts_service.account_role.assign_role(mock_actor, account_id, role.id)
    
    res = accounts_service.account_role.list_roles(mock_actor, account_id)
    assert res.success
    assert len(res.data) == 1
    assert res.data[0].role_id == role.id

    import uuid
    with pytest.raises(AccountNotFound):
        accounts_service.account_role.list_roles(mock_actor, uuid.uuid4())

def test_revoke_role(accounts_service, mock_actor, uow_factory):
    account_id = accounts_service.account.create_account("RevokeRole", "User").data.id
    from src.domains.rbac.entities import Role
    role = Role(name="viewer")
    with uow_factory() as uow:
        role = uow.roles.add(role)
        uow.commit()

    accounts_service.account_role.assign_role(mock_actor, account_id, role.id)

    # Success
    res = accounts_service.account_role.revoke_role(mock_actor, account_id, role.id)
    assert res.success

    # RoleAssignmentNotFound
    with pytest.raises(RoleAssignmentNotFound):
        accounts_service.account_role.revoke_role(mock_actor, account_id, role.id)

def test_get_effective_permissions(accounts_service, mock_actor, uow_factory):
    account_id = accounts_service.account.create_account("Perm", "User").data.id
    from src.domains.rbac.entities import Role
    role = Role(name="manager")
    with uow_factory() as uow:
        role = uow.roles.add(role)
        uow.commit()
    accounts_service.account_role.assign_role(mock_actor, account_id, role.id)

    res = accounts_service.account_role.get_effective_permissions(mock_actor, account_id)
    assert res.success
    assert str(role.id) in res.data

    import uuid
    with pytest.raises(AccountNotFound):
        accounts_service.account_role.get_effective_permissions(mock_actor, uuid.uuid4())

def test_list_for_account(accounts_service, mock_actor, uow_factory):
    account_id = accounts_service.account.create_account("ListForAcc", "User").data.id
    from src.domains.rbac.entities import Role
    role = Role(name="guest")
    with uow_factory() as uow:
        role = uow.roles.add(role)
        uow.commit()

    accounts_service.account_role.assign_role(mock_actor, account_id, role.id)
    
    res = accounts_service.account_role.list_for_account(account_id)
    assert res.success
    assert len(res.data) == 1
    assert res.data[0].role_id == role.id

