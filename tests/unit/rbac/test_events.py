"""Unit tests for RBAC domain events."""

import dataclasses
from uuid import uuid4
import pytest

from src.domains.rbac.events import (
    RoleCreated, RoleUpdated, RoleDeleted,
    PermissionCreated,
    RolePermissionAssigned, RolePermissionRevoked
)

def test_role_created_event_defaults():
    role_id = uuid4()
    event = RoleCreated(role_id=role_id, name="admin")
    
    assert event.role_id == role_id
    assert event.name == "admin"
    assert event.occurred_at is not None

def test_role_updated_event_defaults():
    role_id = uuid4()
    event = RoleUpdated(role_id=role_id, description="new desc")
    
    assert event.role_id == role_id
    assert event.description == "new desc"

def test_role_deleted_event_defaults():
    role_id = uuid4()
    event = RoleDeleted(role_id=role_id, name="admin")
    
    assert event.role_id == role_id
    assert event.name == "admin"

def test_permission_created_event_defaults():
    perm_id = uuid4()
    event = PermissionCreated(permission_id=perm_id, resource="res", action="read")
    
    assert event.permission_id == perm_id
    assert event.resource == "res"
    assert event.action == "read"

def test_role_permission_assigned_event():
    role_id = uuid4()
    perm_id = uuid4()
    event = RolePermissionAssigned(role_id=role_id, permission_id=perm_id)
    
    assert event.role_id == role_id
    assert event.permission_id == perm_id

def test_role_permission_revoked_event():
    role_id = uuid4()
    perm_id = uuid4()
    event = RolePermissionRevoked(role_id=role_id, permission_id=perm_id)
    
    assert event.role_id == role_id
    assert event.permission_id == perm_id

@pytest.mark.parametrize(
    "event",
    [
        RoleCreated(role_id=uuid4(), name="a"),
        RoleUpdated(role_id=uuid4(), description="a"),
        RoleDeleted(role_id=uuid4(), name="a"),
        PermissionCreated(permission_id=uuid4(), resource="r", action="a"),
        RolePermissionAssigned(role_id=uuid4(), permission_id=uuid4()),
        RolePermissionRevoked(role_id=uuid4(), permission_id=uuid4())
    ]
)
def test_rbac_events_are_frozen(event):
    assert dataclasses.is_dataclass(event)
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.role_id = uuid4()  # type: ignore[misc]
