"""API tests for Refund domain."""
from __future__ import annotations

import uuid
import pytest
from flask_jwt_extended import create_access_token

@pytest.fixture
def refund_superuser_headers(app):
    """
    Create authorization headers for an account with sale and refund permissions.
    
    Returns:
        dict: Bearer authorization headers for the privileged account.
    """
    with app.app_context():
        domain_service = app.extensions["domain_service"]
        from tests.conftest import MockActor
        mock_actor = MockActor({"*"})
        unique_suffix = uuid.uuid4().hex[:8]
        
        acc = domain_service.accounts.account.create_account("Admin", "Refund").data
        
        role_res = domain_service.rbac.role.create_role(
            mock_actor, f"refund_admin_{acc.id}_{unique_suffix}", "Refund Admin"
        ).data
        domain_service.accounts.account_role.assign_role(mock_actor, acc.id, role_res.id)
        
        for entity in ["sale", "refund"]:
            for action in ["create", "read", "update", "delete", "list", "process"]:
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
    """
    Create authorization headers for a regular user account.
    
    Parameters:
    	app: The application providing the account service and authentication configuration.
    
    Returns:
    	dict: Headers containing a bearer token for the created account.
    """
    with app.app_context():
        domain_service = app.extensions["domain_service"]
        acc = domain_service.accounts.account.create_account("Normal", "User").data
        token = create_access_token(identity=str(acc.id))
        return {"Authorization": f"Bearer {token}"}

def test_refund_api(client, app, refund_superuser_headers, normal_user_headers, test_variant_id):
    # Unauthenticated
    res = client.post("/api/v1/refunds", json={})
    assert res.status_code == 401

    valid_payload = {
        "sale_id": str(uuid.uuid4()),
        "processed_by": str(uuid.uuid4()),
        "reason": "Customer request",
        "lines": [
            {
                "sale_line_id": str(uuid.uuid4()),
                "quantity": 1
            }
        ]
    }

    # Forbidden
    res = client.post("/api/v1/refunds", headers=normal_user_headers, json=valid_payload)
    assert res.status_code == 403

    # Need a sale to refund.
    variant_id = test_variant_id
    seller_id = str(uuid.uuid4())
    payment_method_id = str(uuid.uuid4())

    sale_res = client.post("/api/v1/sales/checkout", headers=refund_superuser_headers, json={
        "seller_account_id": seller_id,
        "payment_method_id": payment_method_id,
        "customer_name": "Test Customer",
        "discount": 0,
        "lines": [
            {
                "variant_id": variant_id,
                "quantity": 2,
                "unit_price": 500,
                "discount": 0
            }
        ]
    })
    
    assert sale_res.status_code == 201
    sale_data = sale_res.get_json()["data"]
    sale_id = sale_data["id"]
    sale_line_id = sale_data["lines"][0]["id"]
    
    # Complete sale so we can refund it
    client.post(f"/api/v1/sales/{sale_id}/complete", headers=refund_superuser_headers)

    processed_by = str(uuid.uuid4())

    # Create Refund
    res = client.post("/api/v1/refunds", headers=refund_superuser_headers, json={
        "sale_id": sale_id,
        "processed_by": processed_by,
        "reason": "Customer request",
        "lines": [
            {
                "sale_line_id": sale_line_id,
                "quantity": 1
            }
        ]
    })
    
    assert res.status_code == 201
    refund_data = res.get_json()["data"]
    assert refund_data["sale_id"] == sale_id
    assert refund_data["status"] == "pending"
    assert refund_data["reason"] == "Customer request"
    assert len(refund_data["lines"]) == 1
    assert refund_data["lines"][0]["quantity"] == 1
