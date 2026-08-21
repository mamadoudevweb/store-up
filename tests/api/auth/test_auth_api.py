"""API tests for Auth domain."""
from __future__ import annotations

import pytest


@pytest.fixture
def auth_setup(app):
    with app.app_context():
        domain_service = app.extensions["domain_service"]
        
        # Fake a mock_actor for credential setting
        from src.core.services.base_service import SupportsPermissionCheck
        class MockActor(SupportsPermissionCheck):
            def has_permission(self, domain, entity, action): return True
            
        import uuid
        username = f"authuser_{uuid.uuid4().hex[:8]}"
        email = f"{username}@test.com"
        acc = domain_service.accounts.account.create_account("Auth", "User").data
        domain_service.accounts.credential.set_credentials(
            acc.id, username, email, "password"
        )
        return username, "password"


def test_login(client, auth_setup):
    username, password = auth_setup
    
    # Valid login
    res = client.post("/api/v1/auth/login", json={
        "username": username,
        "password": password
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    
    # Invalid login
    res = client.post("/api/v1/auth/login", json={
        "username": username,
        "password": "wrongpassword"
    })
    assert res.status_code == 401


def test_refresh_and_logout(client, auth_setup):
    username, password = auth_setup
    
    login_res = client.post("/api/v1/auth/login", json={
        "username": username,
        "password": password
    })
    tokens = login_res.get_json()["data"]
    
    # Refresh
    refresh_res = client.post("/api/v1/auth/refresh", headers={
        "Authorization": f"Bearer {tokens['refresh_token']}"
    })
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.get_json()["data"]
    
    # Logout
    logout_res = client.post("/api/v1/auth/logout", headers={
        "Authorization": f"Bearer {tokens['access_token']}"
    })
    assert logout_res.status_code == 200
    
    # Try using token again, it should fail (though logout uses a denylist, let's assume it works)
    # Testing JWT blacklist integration via client call requires a protected route
    # Let's test a simple protected route
    test_res = client.get("/api/v1/accounts", headers={
        "Authorization": f"Bearer {tokens['access_token']}"
    })
    assert test_res.status_code == 401  # Revoked token
