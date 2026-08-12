"""Integration tests for RbacService."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app.extensions import db
from src.domains.rbac.exceptions import (
    PermissionAlreadyExists,
    RoleAlreadyExists,
    RoleNotFound,
    PermissionNotFound,
)
from src.domains.rbac.repositories.sql.sql_uow import SqlRbacUnitOfWork
from src.domains.rbac.services import RbacService
from src.domains.shared.events import EventBus


@pytest.fixture(scope="module")
def rbac_engine():
    engine = create_engine("sqlite:///:memory:")
    # Import ORMs to register with metadata
    from src.domains.rbac.repositories.sql.orms import (
        role_model, permission_model, role_permission_model
    )
    db.Model.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def rbac_uow_factory(rbac_engine):
    return sessionmaker(bind=rbac_engine)


@pytest.fixture
def rbac_service(rbac_uow_factory):
    uow = SqlRbacUnitOfWork(rbac_uow_factory)
    bus = EventBus()
    return RbacService(uow, bus)


def test_create_role(rbac_service):
    res = rbac_service.role.create_role("admin", "Full access")
    assert res.success
    assert res.data.name == "admin"


def test_create_role_duplicate_raises(rbac_service):
    rbac_service.role.create_role("moderator")
    with pytest.raises(RoleAlreadyExists):
        rbac_service.role.create_role("moderator")


def test_get_role(rbac_service):
    created = rbac_service.role.create_role("viewer").data
    fetched = rbac_service.role.get_role(created.id).data
    assert fetched.id == created.id
    assert fetched.name == "viewer"


def test_get_role_not_found(rbac_service):
    import uuid
    with pytest.raises(RoleNotFound):
        rbac_service.role.get_role(uuid.uuid4())


def test_create_permission(rbac_service):
    res = rbac_service.permission.create_permission("products", "read")
    assert res.success
    assert res.data.name == "products:read"


def test_create_permission_duplicate_raises(rbac_service):
    rbac_service.permission.create_permission("orders", "write")
    with pytest.raises(PermissionAlreadyExists):
        rbac_service.permission.create_permission("orders", "write")


def test_assign_and_check_permission(rbac_service):
    role = rbac_service.role.create_role("editor").data
    perm = rbac_service.permission.create_permission("articles", "write").data

    rbac_service.role_permission.assign(role.id, perm.id)

    result = rbac_service.permission.check_roles_have_permission(
        [role.id], "articles", "write"
    )
    assert result.success
    assert result.data is True


def test_check_permission_not_assigned(rbac_service):
    role = rbac_service.role.create_role("guest").data
    rbac_service.permission.create_permission("products", "delete")

    result = rbac_service.permission.check_roles_have_permission(
        [role.id], "products", "delete"
    )
    assert result.success
    assert result.data is False


def test_revoke_permission(rbac_service):
    role = rbac_service.role.create_role("temp_role").data
    perm = rbac_service.permission.create_permission("reports", "read").data

    rbac_service.role_permission.assign(role.id, perm.id)

    # Confirm assigned
    result_before = rbac_service.permission.check_roles_have_permission(
        [role.id], "reports", "read"
    )
    assert result_before.data is True

    # Revoke
    rbac_service.role_permission.revoke(role.id, perm.id)

    result_after = rbac_service.permission.check_roles_have_permission(
        [role.id], "reports", "read"
    )
    assert result_after.data is False
