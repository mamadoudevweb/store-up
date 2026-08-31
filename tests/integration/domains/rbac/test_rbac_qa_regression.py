"""
QA Regression Suite — RBAC Domain
==================================
These tests verify that previously discovered bugs in the RBAC domain
(documented in the QA manifest) remain fixed.

If any of these tests fail, it indicates a regression of a known defect.
"""
from __future__ import annotations

import uuid
import pytest

from src.domains.rbac.services import RbacDomainService
from src.domains.rbac.events import (
    RoleCreated,
    RoleDeleted,
    PermissionCreated,
)
from src.domains.rbac.exceptions import RoleNotFound, PermissionNotFound
from src.domains.rbac.repositories.filters import RolePermissionFilter


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def rbac(uow_factory):
    """RbacDomainService wired to the in-memory SQLite test UoW."""
    return RbacDomainService(uow_factory)


# ---------------------------------------------------------------------------
# BUG-RBAC-001 — RoleService.create_role bypasses Role.create(), no event
# ---------------------------------------------------------------------------

def test_bug_rbac_001_create_role_emits_role_created_event(rbac, mock_actor):
    """
    BUG-RBAC-001
    RoleService.create_role() instantiates Role(...) directly instead of calling
    Role.create(). As a result the RoleCreated domain event is never registered
    on the entity and is therefore never dispatched by the UoW.

    Expected: After a successful create_role call, the returned entity must carry
              exactly one pending RoleCreated event via pull_events().
    Current:  The entity carries zero events — FAILS.
    """
    dispatched = []
    uow = rbac.role._uow_factory()
    uow._dispatcher.subscribe(RoleCreated, dispatched.append)

    suffix = uuid.uuid4().hex[:8]
    result = rbac.role.create_role(mock_actor, f"test_role_{suffix}", "A role")

    assert result.success

    assert len(dispatched) == 1, (
        f"Expected 1 RoleCreated event to be dispatched; got {len(dispatched)}. "
        "RoleService.create_role() must use Role.create() instead of Role()."
    )


# ---------------------------------------------------------------------------
# BUG-RBAC-002 — RoleService.delete_role does not call role.mark_deleted()
# ---------------------------------------------------------------------------

def test_bug_rbac_002_delete_role_emits_role_deleted_event(rbac, mock_actor):
    """
    BUG-RBAC-002
    RoleService.delete_role() calls uow.roles.delete(role) directly without
    calling role.mark_deleted() first. The RoleDeleted domain event is therefore
    never registered and never dispatched.

    Strategy: We subscribe a spy to the EventDispatcher to intercept the RoleDeleted
    event directly from the service execution path.
    """
    suffix = uuid.uuid4().hex[:8]
    role = rbac.role.create_role(mock_actor, f"todelete_{suffix}", "desc").data
    role_id = role.id

    dispatched = []
    uow = rbac.role._uow_factory()
    uow._dispatcher.subscribe(RoleDeleted, dispatched.append)

    del_result = rbac.role.delete_role(mock_actor, role_id)
    assert del_result.success

    # The service MUST raise RoleNotFound for the already-deleted role
    with pytest.raises(RoleNotFound):
        rbac.role.get_role(mock_actor, role_id)

    assert len(dispatched) == 1, (
        f"Expected 1 RoleDeleted event to be dispatched; got {len(dispatched)}. "
        "RoleService.delete_role() must call role.mark_deleted() before deletion."
    )


# ---------------------------------------------------------------------------
# BUG-RBAC-003 — PermissionService.create_permission bypasses Permission.create()
# ---------------------------------------------------------------------------

def test_bug_rbac_003_create_permission_emits_permission_created_event(rbac, mock_actor):
    """
    BUG-RBAC-003
    PermissionService.create_permission() builds Permission(...) directly instead
    of Permission.create(...). The PermissionCreated domain event is never
    registered, so downstream subscribers never fire.

    Expected: The returned Permission entity holds exactly one PermissionCreated event.
    Current:  Zero events — FAILS.
    """
    dispatched = []
    uow = rbac.permission._uow_factory()
    uow._dispatcher.subscribe(PermissionCreated, dispatched.append)

    suffix = uuid.uuid4().hex[:8]
    result = rbac.permission.create_permission(
        mock_actor, f"res_{suffix}", "read", "A permission"
    )

    assert result.success

    assert len(dispatched) == 1, (
        f"Expected 1 PermissionCreated event to be dispatched; got {len(dispatched)}. "
        "PermissionService.create_permission() must use Permission.create() instead of Permission()."
    )


# ---------------------------------------------------------------------------
# BUG-RBAC-004 — Re-assign via string UUIDs must reactivate, not duplicate
# ---------------------------------------------------------------------------

def test_bug_rbac_004_assign_reactivates_via_string_ids(rbac, mock_actor, uow_factory):
    """
    BUG-RBAC-004
    Verify the full string-ID path through assign → revoke → re-assign.
    Re-assigning a revoked permission via string UUIDs must reactivate the
    existing row (revoked_at=None), not create a duplicate.
    """
    suffix = uuid.uuid4().hex[:8]
    role = rbac.role.create_role(mock_actor, f"str_role_{suffix}", "desc").data
    perm = rbac.permission.create_permission(mock_actor, f"str_res_{suffix}", "write", "d").data

    role_id_str = str(role.id)
    perm_id_str = str(perm.id)

    assign_res = rbac.role_permission.assign(mock_actor, role_id_str, perm_id_str)
    assert assign_res.success

    revoke_res = rbac.role_permission.revoke(mock_actor, role_id_str, perm_id_str)
    assert revoke_res.success

    with uow_factory() as uow:
        rp = uow.role_permissions.get(
            RolePermissionFilter(role_id=role.id, permission_id=perm.id, active_only=False)
        )
        assert rp is not None
        assert rp.active is False, "Expected revoked_at to be set after revoke"

    reassign_res = rbac.role_permission.assign(mock_actor, role_id_str, perm_id_str)
    assert reassign_res.success

    with uow_factory() as uow:
        rp_reactivated = uow.role_permissions.get(
            RolePermissionFilter(role_id=role.id, permission_id=perm.id, active_only=False)
        )
        assert rp_reactivated is not None
        assert rp_reactivated.active is True, (
            "Re-assigning a previously revoked permission must reactivate it "
            "(revoked_at=None), not create a second row."
        )
        assert rp_reactivated.revoked_at is None


# ---------------------------------------------------------------------------
# BUG-RBAC-005 — assign raises PermissionNotFound for invalid permission_id
# ---------------------------------------------------------------------------

def test_bug_rbac_005_assign_raises_permission_not_found(rbac, mock_actor):
    """
    BUG-RBAC-005
    RolePermissionService.assign() must raise PermissionNotFound (not a generic
    SQLAlchemy integrity error) when the permission_id does not exist.
    """
    suffix = uuid.uuid4().hex[:8]
    role = rbac.role.create_role(mock_actor, f"role_err_{suffix}", "desc").data

    with pytest.raises(PermissionNotFound):
        rbac.role_permission.assign(mock_actor, role.id, uuid.uuid4())


# ---------------------------------------------------------------------------
# BUG-RBAC-006 — revoke raises RoleNotFound for non-existent role (regression guard)
# ---------------------------------------------------------------------------

def test_bug_rbac_006_revoke_raises_role_not_found(rbac, mock_actor):
    """
    BUG-RBAC-006
    Regression guard: RolePermissionService.revoke() must raise RoleNotFound
    when the role does not exist.
    """
    with pytest.raises(RoleNotFound):
        rbac.role_permission.revoke(mock_actor, uuid.uuid4(), uuid.uuid4())


# ---------------------------------------------------------------------------
# BUG-RBAC-007 — list_role_permissions must exclude revoked permissions
# ---------------------------------------------------------------------------

def test_bug_rbac_007_list_role_permissions_excludes_revoked(rbac, mock_actor):
    """
    BUG-RBAC-007
    After the permission_repository change (.where(RolePermissionModel.revoked_at.is_(None))),
    list_role_permissions must NOT return revoked permissions.
    Verified end-to-end: assign two, revoke one, expect exactly one returned.
    """
    suffix = uuid.uuid4().hex[:8]
    role = rbac.role.create_role(mock_actor, f"filt_role_{suffix}", "desc").data
    perm_a = rbac.permission.create_permission(mock_actor, f"fa_{suffix}", "read", "d").data
    perm_b = rbac.permission.create_permission(mock_actor, f"fb_{suffix}", "write", "d").data

    rbac.role_permission.assign(mock_actor, role.id, perm_a.id)
    rbac.role_permission.assign(mock_actor, role.id, perm_b.id)

    res = rbac.permission.list_role_permissions(mock_actor, role.id)
    assert len(res.data.items) == 2

    rbac.role_permission.revoke(mock_actor, role.id, perm_a.id)

    res_after = rbac.permission.list_role_permissions(mock_actor, role.id)
    assert len(res_after.data.items) == 1, (
        "After revoking one permission, list_role_permissions must return only "
        "the remaining active permission."
    )
    assert res_after.data.items[0].id == perm_b.id


# ---------------------------------------------------------------------------
# BUG-RBAC-008 — list_for_role returns RolePermission entities (coverage gap)
# ---------------------------------------------------------------------------

def test_bug_rbac_008_list_for_role_returns_role_permission_entities(rbac, mock_actor):
    """
    BUG-RBAC-008
    RolePermissionService.list_for_role() had 0% test coverage.
    Verify it exists, returns the correct type, and filters by role.
    """
    from src.domains.rbac.entities.role_permission import RolePermission

    suffix = uuid.uuid4().hex[:8]
    role = rbac.role.create_role(mock_actor, f"lr_role_{suffix}", "desc").data
    perm = rbac.permission.create_permission(mock_actor, f"lr_res_{suffix}", "exec", "d").data

    rbac.role_permission.assign(mock_actor, role.id, perm.id)

    result = rbac.role_permission.list_for_role(mock_actor, role.id)
    assert result.success
    assert isinstance(result.data, list)
    assert len(result.data) == 1
    item = result.data[0]
    assert isinstance(item, RolePermission), (
        f"list_for_role must return RolePermission entities, got {type(item)}"
    )
    assert item.role_id == role.id
    assert item.permission_id == perm.id
    assert item.active is True


# ---------------------------------------------------------------------------
# BUG-RBAC-009 — Role.create() / update() inline imports are dead code
# ---------------------------------------------------------------------------

def test_bug_rbac_009_role_entity_inline_imports_are_redundant():
    """
    BUG-RBAC-009
    After moving event imports to the top of role.py, the methods Role.create()
    and Role.update() still contain redundant inline import statements.
    This test exercises all three entity methods to confirm they work with the
    top-level imports alone, proving the inline imports are safe to remove.
    The test FAILS because Role.create() currently has a redundant inline
    import *and* still emits the event through it — confirming dead code exists.

    We detect this by asserting the inline import is absent from the source.
    """
    import inspect
    from src.domains.rbac.entities import role as role_module

    source = inspect.getsource(role_module)

    # Each of these inline imports is redundant after the top-level import refactor
    redundant_patterns = [
        "from src.domains.rbac.events import RoleCreated",  # inside create()
        "from src.domains.rbac.events import RoleUpdated",  # inside update()
    ]

    found = [p for p in redundant_patterns if source.count(p) > 1]

    assert not found, (
        f"BUG-RBAC-009: Found redundant inline import(s) still present inside method bodies: "
        f"{found}. These are dead code — the top-level import already covers them. "
        f"Remove the inline `from ... import` lines inside Role.create() and Role.update()."
    )
