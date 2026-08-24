"""API tests for Sale domain."""
from __future__ import annotations

import uuid
import pytest
from flask_jwt_extended import create_access_token

@pytest.fixture
def sale_superuser_headers(app):
    with app.app_context():
        domain_service = app.extensions["domain_service"]
        from tests.conftest import MockActor
        mock_actor = MockActor({"*"})
        unique_suffix = uuid.uuid4().hex[:8]
        
        acc = domain_service.accounts.account.create_account("Admin", "Sale").data
        
        role_res = domain_service.rbac.role.create_role(
            mock_actor, f"sale_admin_{acc.id}_{unique_suffix}", "Sale Admin"
        ).data
        domain_service.accounts.account_role.assign_role(mock_actor, acc.id, role_res.id)
        
        # Grant permissions for sale and refund
        for entity in ["sale", "refund"]:
            for action in ["create", "read", "update", "delete", "list", "complete", "fail"]:
                resource_name = f"sale:{entity}"
                from src.domains.rbac.exceptions import PermissionAlreadyExists
                try:
                    perm = domain_service.rbac.permission.create_permission(
                        mock_actor, resource_name, action, "All perms"
                    ).data
                except PermissionAlreadyExists:
                    from src.domains.rbac.repositories.filters import PermissionFilter
                    with domain_service.rbac.permission._uow_factory() as uow:
                        res = uow.permissions.list(PermissionFilter(resource=resource_name, action=action))
                        perm = res.items[0]
                domain_service.rbac.role_permission.assign(mock_actor, role_res.id, perm.id)

        token = create_access_token(identity=str(acc.id))
        return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def normal_user_headers(app):
    with app.app_context():
        domain_service = app.extensions["domain_service"]
        acc = domain_service.accounts.account.create_account("Normal", "User").data
        token = create_access_token(identity=str(acc.id))
        return {"Authorization": f"Bearer {token}"}

def test_sale_api(client, app, sale_superuser_headers, normal_user_headers, test_variant_id):
    # Unauthenticated
    res = client.post("/api/v1/sales/checkout", json={})
    assert res.status_code == 401
    
    variant_id = test_variant_id

    seller_id = str(uuid.uuid4())
    payment_method_id = str(uuid.uuid4())

    valid_payload = {
        "seller_account_id": seller_id,
        "payment_method_id": payment_method_id,
        "customer_name": "Test Customer",
        "discount": 100,
        "lines": [
            {
                "variant_id": variant_id,
                "quantity": 2,
                "unit_price": 500,
                "discount": 50
            }
        ]
    }

    # Forbidden
    res = client.post("/api/v1/sales/checkout", headers=normal_user_headers, json=valid_payload)
    assert res.status_code == 403
    # Create Sale (Checkout)
    res = client.post("/api/v1/sales/checkout", headers=sale_superuser_headers, json=valid_payload)
    assert res.status_code == 201, res.get_json()
    sale_data = res.get_json()["data"]
    sale_id = sale_data["id"]
    assert sale_data["total"] == 800  # (2*500) - 100 - (50*2)? Wait, lines discount vs total discount. Subtotal = 2*500 - 100 = 900. Total = 900 - 100 = 800
    assert sale_data["status"] == "pending"

    # Complete Sale
    res = client.post(f"/api/v1/sales/{sale_id}/complete", headers=sale_superuser_headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["status"] == "completed"

    # Fail Sale (should fail as it's already completed)
    res = client.post(f"/api/v1/sales/{sale_id}/fail", headers=sale_superuser_headers)
    assert res.status_code == 409  # ConflictError

    # Create another Sale for failure
    res2 = client.post("/api/v1/sales/checkout", headers=sale_superuser_headers, json={
        "seller_account_id": seller_id,
        "payment_method_id": payment_method_id,
        "customer_name": "Test Customer 2",
        "discount": 0,
        "lines": [
            {
                "variant_id": variant_id,
                "quantity": 1,
                "unit_price": 100,
                "discount": 0
            }
        ]
    })
    sale2_id = res2.get_json()["data"]["id"]

    # Fail Sale
    res2_fail = client.post(f"/api/v1/sales/{sale2_id}/fail", headers=sale_superuser_headers)
    assert res2_fail.status_code == 200
    assert res2_fail.get_json()["data"]["status"] == "failed"
    