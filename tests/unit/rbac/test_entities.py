"""Unit tests for RBAC domain entities."""

from uuid import uuid4
import pytest

from src.domains.rbac.entities.role import Role
from src.domains.rbac.entities.permission import Permission
from src.domains.rbac.entities.role_permission import RolePermission
from src.domains.rbac.events import (
    RoleCreated, RoleUpdated, RoleDeleted,
    PermissionCreated,
    RolePermissionAssigned, RolePermissionRevoked
)

def test_role_creation():
    role = Role.create("admin", "Admin role")
    assert role.name == "admin"
    assert role.description == "Admin role"
    
    events = role.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], RoleCreated)
    assert events[0].name == "admin"

def test_role_update():
    role = Role.create("admin", "Admin role")
    role.pull_events()
    
    role.update("Super Admin")
    assert role.name == "admin"
    assert role.description == "Super Admin"
    
    events = role.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], RoleUpdated)
    assert events[0].role_id == role.id

def test_role_deletion():
    role = Role.create("admin", "Admin role")
    role.pull_events()
    
    role.mark_deleted()
    
    events = role.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], RoleDeleted)
    assert events[0].role_id == role.id
    assert events[0].name == "admin"

def test_permission_creation():
    perm = Permission.create("catalog:product", "write", "Can write products")
    assert perm.resource == "catalog:product"
    assert perm.action == "write"
    
    events = perm.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], PermissionCreated)
    assert events[0].resource == "catalog:product"
    assert events[0].action == "write"

def test_role_permission_assignment():
    role_id = uuid4()
    permission_id = uuid4()
    
    rp = RolePermission.assign_permission(role_id, permission_id)
    
    assert rp.role_id == role_id
    assert rp.permission_id == permission_id
    assert rp.revoked_at is None
    assert rp.active is True
    
    events = rp.pull_events()
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, RolePermissionAssigned)
    assert event.role_id == role_id
    assert event.permission_id == permission_id

def test_role_permission_revocation():
    role_id = uuid4()
    permission_id = uuid4()
    
    rp = RolePermission.assign_permission(role_id, permission_id)
    rp.pull_events()  # Clear initial events
    
    rp.revoke_permission()
    
    assert rp.revoked_at is not None
    assert rp.active is False
    
    events = rp.pull_events()
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, RolePermissionRevoked)
    assert event.role_id == role_id
    assert event.permission_id == permission_id

def test_role_permission_reactivation():
    role_id = uuid4()
    permission_id = uuid4()
    
    rp = RolePermission.assign_permission(role_id, permission_id)
    rp.revoke_permission()
    rp.pull_events()  # Clear events
    
    rp.reactivate()
    
    assert rp.revoked_at is None
    assert rp.active is True
    
    events = rp.pull_events()
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, RolePermissionAssigned)
    assert event.role_id == role_id
    assert event.permission_id == permission_id
