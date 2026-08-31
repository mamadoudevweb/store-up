"""Integration tests for RBAC domain services."""
from __future__ import annotations

import pytest
import uuid
from uuid import UUID

from src.domains.rbac.services import RbacDomainService
from src.domains.rbac.services.role import RoleService
from src.domains.rbac.services.permission import PermissionService
from src.domains.rbac.services.role_permission import RolePermissionService
from src.domains.rbac.exceptions import (
    RoleAlreadyExists, RoleNotFound, 
    PermissionAlreadyExists, PermissionNotFound
)
from src.domains.rbac.repositories.filters import RolePermissionFilter

@pytest.fixture
def rbac_service(uow_factory):
    """Provides the RbacDomainService using the test UoW."""
    return RbacDomainService(uow_factory)


def test_create_and_get_role(rbac_service, mock_actor):
    res = rbac_service.role.create_role(mock_actor, "admin_test_rbac", "Administrator role test")
    assert res.success
    role_id = res.data.id
    
    get_res = rbac_service.role.get_role(mock_actor, role_id)
    assert get_res.success
    assert get_res.data.name == "admin_test_rbac"


def test_create_permission_and_assign(rbac_service, mock_actor):
    unique_suffix = uuid.uuid4().hex[:8]
    role_res = rbac_service.role.create_role(mock_actor, f"editor_{unique_suffix}", "Editor role")
    role_id = role_res.data.id

    perm_res = rbac_service.permission.create_permission(
        mock_actor, f"catalog:product:{unique_suffix}", "create", "Create products"
    )
    perm_id = perm_res.data.id

    # Assign
    assign_res = rbac_service.role_permission.assign(mock_actor, role_id, perm_id)
    assert assign_res.success

    # List permissions for role
    list_res = rbac_service.permission.list_role_permissions(mock_actor, role_id)
    assert list_res.success
    perms = list_res.data
    assert len(perms.items) == 1
    assert perms.items[0].action == "create"

    # Check permission logic directly
    has_perm = rbac_service.permission.check_roles_have_permission([role_id], f"catalog:product:{unique_suffix}", "create")
    assert has_perm.data is True

    has_perm2 = rbac_service.permission.check_roles_have_permission([role_id], f"catalog:product:{unique_suffix}", "delete")
    assert has_perm2.data is False


def test_role_errors_and_delete(rbac_service, mock_actor):
    unique_suffix = uuid.uuid4().hex[:8]
    # Create role
    res = rbac_service.role.create_role(mock_actor, f"dup_{unique_suffix}", "desc")
    assert res.success
    role_id = res.data.id

    # Duplicate name should fail
    with pytest.raises(RoleAlreadyExists):
        rbac_service.role.create_role(mock_actor, f"dup_{unique_suffix}", "desc")

    # Get non-existent
    with pytest.raises(RoleNotFound):
        rbac_service.role.get_role(mock_actor, uuid.uuid4())

    # Delete
    del_res = rbac_service.role.delete_role(mock_actor, role_id)
    assert del_res.success
    
    # Get after delete
    with pytest.raises(RoleNotFound):
        rbac_service.role.get_role(mock_actor, role_id)

    # Delete non-existent
    with pytest.raises(RoleNotFound):
        rbac_service.role.delete_role(mock_actor, role_id)


def test_permission_errors_and_delete(rbac_service, mock_actor):
    unique_suffix = uuid.uuid4().hex[:8]
    
    # Create permission
    res = rbac_service.permission.create_permission(mock_actor, f"res:{unique_suffix}", "read", "desc")
    assert res.success
    perm_id = res.data.id

    # Duplicate should fail
    with pytest.raises(PermissionAlreadyExists):
        rbac_service.permission.create_permission(mock_actor, f"res:{unique_suffix}", "read", "desc")

    # Get non-existent
    with pytest.raises(PermissionNotFound):
        rbac_service.permission.get_permission(mock_actor, uuid.uuid4())

    # Delete
    del_res = rbac_service.permission.delete_permission(mock_actor, perm_id)
    assert del_res.success

    # Get after delete
    with pytest.raises(PermissionNotFound):
        rbac_service.permission.get_permission(mock_actor, perm_id)

    # Delete non-existent
    with pytest.raises(PermissionNotFound):
        rbac_service.permission.delete_permission(mock_actor, perm_id)


def test_role_permission_unassign(rbac_service, mock_actor, uow_factory):
    unique_suffix = uuid.uuid4().hex[:8]
    
    role = rbac_service.role.create_role(mock_actor, f"role_{unique_suffix}", "desc").data
    perm = rbac_service.permission.create_permission(mock_actor, f"res_{unique_suffix}", "write", "desc").data
    
    rbac_service.role_permission.assign(mock_actor, role.id, perm.id)
    assert len(rbac_service.permission.list_role_permissions(mock_actor, role.id).data.items) == 1
    
    # Check it exists and is active
    with uow_factory() as uow:
        rp = uow.role_permissions.get(RolePermissionFilter(role_id=role.id, permission_id=perm.id, active_only=False))
        assert rp is not None
        assert rp.active is True
        assert rp.revoked_at is None

    # Unassign
    res = rbac_service.role_permission.revoke(mock_actor, role.id, perm.id)
    assert res.success
    assert len(rbac_service.permission.list_role_permissions(mock_actor, role.id).data.items) == 0

    # Verify the row is not deleted, but revoked_at is set
    with uow_factory() as uow:
        rp_revoked = uow.role_permissions.get(RolePermissionFilter(role_id=role.id, permission_id=perm.id, active_only=False))
        assert rp_revoked is not None
        assert rp_revoked.active is False
        assert rp_revoked.revoked_at is not None

    # Unassign non-existent (idempotent, shouldn't fail)
    res2 = rbac_service.role_permission.revoke(mock_actor, role.id, perm.id)
    assert res2.success

    # Assign duplicate / reactivate (should work and reset revoked_at)
    rbac_service.role_permission.assign(mock_actor, role.id, perm.id)
    with uow_factory() as uow:
        rp_reactivated = uow.role_permissions.get(RolePermissionFilter(role_id=role.id, permission_id=perm.id, active_only=False))
        assert rp_reactivated is not None
        assert rp_reactivated.active is True
        assert rp_reactivated.revoked_at is None

    res3 = rbac_service.role_permission.assign(mock_actor, role.id, perm.id)
    assert res3.success
