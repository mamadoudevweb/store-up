"""API tests for RBAC domain."""
from __future__ import annotations

import pytest
from flask_jwt_extended import create_access_token


@pytest.fixture
def superuser_headers(app):
    with app.app_context():
        # Setup a full superuser actor
        domain_service = app.extensions["domain_service"]
        acc = domain_service.accounts.account.create_account("Admin", "Super").data
        
        # Give them the rbac bypass role (if we had one) or we just use a mock actor.
        # However, the API uses the identity in the token. We can monkeypatch get_current_actor
        # during the test, or just grant them actual permissions.
        # Let's grant them the actual permissions for the tests.
        role_res = domain_service.rbac.role.create_role(
            None, f"super_admin_{acc.id}", "Super Admin"
        ).data
        domain_service.accounts.account_role.assign_role(None, acc.id, role_res.id)
        
        # Grant permissions
        for entity in ["role", "permission", "role_permission"]:
            for action in ["create", "read", "update", "delete", "list", "assign"]:
                perm = domain_service.rbac.permission.create_permission(
                    None, f"rbac:{entity}", action, "All perms"
                ).data
                domain_service.rbac.role_permission.assign(None, role_res.id, perm.id)

        token = create_access_token(identity=str(acc.id))
        return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def normal_user_headers(app):
    with app.app_context():
        domain_service = app.extensions["domain_service"]
        acc = domain_service.accounts.account.create_account("Normal", "User").data
        token = create_access_token(identity=str(acc.id))
        return {"Authorization": f"Bearer {token}"}


def test_role_api(client, superuser_headers, normal_user_headers):
    # Create role without auth
    res = client.post("/api/v1/roles", json={"name": "test_role", "description": "A test role"})
    assert res.status_code == 401

    # Create role with normal user (403)
    res = client.post("/api/v1/roles", headers=normal_user_headers, json={
        "name": "test_role_x", "description": "A test role"
    })
    assert res.status_code == 403

    # Create role with superuser
    res = client.post("/api/v1/roles", headers=superuser_headers, json={
        "name": "test_role_api", "description": "A test role"
    })
    assert res.status_code == 201
    role_id = res.get_json()["data"]["id"]

    # Get role
    res = client.get(f"/api/v1/roles/{role_id}", headers=superuser_headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["name"] == "test_role_api"

    # List roles
    res = client.get("/api/v1/roles", headers=superuser_headers)
    assert res.status_code == 200
    assert len(res.get_json()["data"]["items"]) > 0

    # Delete role
    res = client.delete(f"/api/v1/roles/{role_id}", headers=superuser_headers)
    assert res.status_code == 200

    # Get deleted role -> 404
    res = client.get(f"/api/v1/roles/{role_id}", headers=superuser_headers)
    assert res.status_code == 404


def test_permission_api(client, superuser_headers, normal_user_headers):
    import uuid
    res_name = f"res_{uuid.uuid4().hex[:8]}"

    # Create permission
    res = client.post("/api/v1/permissions", headers=superuser_headers, json={
        "resource": res_name,
        "action": "read",
        "description": "Read resource"
    })
    assert res.status_code == 201
    perm_id = res.get_json()["data"]["id"]

    # Get permission
    res = client.get(f"/api/v1/permissions/{perm_id}", headers=superuser_headers)
    assert res.status_code == 200

    # List permissions
    res = client.get("/api/v1/permissions", headers=superuser_headers)
    assert res.status_code == 200

    # Delete permission
    res = client.delete(f"/api/v1/permissions/{perm_id}", headers=superuser_headers)
    assert res.status_code == 200


def test_role_permission_api(client, superuser_headers):
    import uuid
    suffix = uuid.uuid4().hex[:8]

    # Create role
    role_res = client.post("/api/v1/roles", headers=superuser_headers, json={
        "name": f"role_{suffix}", "description": "desc"
    })
    role_id = role_res.get_json()["data"]["id"]

    # Create perm
    perm_res = client.post("/api/v1/permissions", headers=superuser_headers, json={
        "resource": f"res_{suffix}", "action": "write", "description": "desc"
    })
    perm_id = perm_res.get_json()["data"]["id"]

    # Assign
    res = client.post(f"/api/v1/roles/{role_id}/permissions", headers=superuser_headers, json={
        "permission_id": perm_id
    })
    assert res.status_code == 201

    # List role permissions
    res = client.get(f"/api/v1/roles/{role_id}/permissions", headers=superuser_headers)
    assert res.status_code == 200
    assert len(res.get_json()["data"]["items"]) == 1

    # Unassign
    res = client.delete(f"/api/v1/roles/{role_id}/permissions/{perm_id}", headers=superuser_headers)
    assert res.status_code == 200

    # List role permissions (empty)
    res = client.get(f"/api/v1/roles/{role_id}/permissions", headers=superuser_headers)
    assert res.status_code == 200
    assert len(res.get_json()["data"]["items"]) == 0
