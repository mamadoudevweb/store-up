"""Integration tests for RBAC domain services."""
from __future__ import annotations

import pytest
from uuid import UUID

from src.domains.rbac.services import RbacDomainService
from src.domains.rbac.services.role import RoleService
from src.domains.rbac.services.permission import PermissionService
from src.domains.rbac.services.role_permission import RolePermissionService


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
    role_res = rbac_service.role.create_role(mock_actor, "editor", "Editor role")
    role_id = role_res.data.id

    perm_res = rbac_service.permission.create_permission(
        mock_actor, "catalog:product", "create", "Create products"
    )
    perm_id = perm_res.data.id

    # Assign
    assign_res = rbac_service.role_permission.assign(mock_actor, role_id, perm_id)
    assert assign_res.success

    # List permissions for role
    list_res = rbac_service.permission.list_role_permissions(mock_actor, role_id)
    assert list_res.success
    perms = list_res.data
    assert len(perms) == 1
    assert perms[0].action == "create"

    # Check permission logic directly
    has_perm = rbac_service.permission.check_roles_have_permission([role_id], "catalog:product", "create")
    assert has_perm is True

    has_perm2 = rbac_service.permission.check_roles_have_permission([role_id], "catalog:product", "delete")
    assert has_perm2 is False
