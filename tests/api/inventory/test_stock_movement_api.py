import uuid

import pytest

@pytest.fixture
def product_id():
    return uuid.uuid4()

@pytest.fixture
def stock_movement(app, uow_factory, product_id):
    with app.app_context():
        from src.domains.inventory.entities import StockMovement
        movement = StockMovement.create(
            product_id=product_id,
            quantity_change=10,
            reason="INITIAL_STOCK",
        )
        with uow_factory() as uow:
            movement = uow.stock_movements.add(movement)
            uow.commit()
            
        return movement

@pytest.fixture
def inventory_superuser_headers(app, uow_factory):
    with app.app_context():
        domain_service = app.extensions["domain_service"]
        from tests.conftest import MockActor
        mock_actor = MockActor({"*"})
        unique_suffix = uuid.uuid4().hex[:8]
        
        acc = domain_service.accounts.account.create_account("Admin", "Inventory").data
        role = domain_service.rbac.role.create_role(mock_actor, f"inv_admin_{unique_suffix}", "Inventory Admin").data
        
        # Manually create permissions using UOW since service doesn't have get_by_name
        from src.domains.rbac.repositories.filters import PermissionFilter
        from src.domains.rbac.entities import Permission
        
        perms_to_create = [
            ("inventory:inventory_item", "read"),
            ("inventory:inventory_item", "update"),
            ("inventory:stock_movement", "read"),
            ("inventory:stock_movement", "update"),
        ]
        
        for resource, action in perms_to_create:
            with uow_factory() as uow:
                perm = uow.permissions.get(PermissionFilter(resource=resource, action=action))
                if not perm:
                    perm = Permission(resource=resource, action=action, description="Full access")
                    perm = uow.permissions.add(perm)
                    uow.commit()
                domain_service.rbac.role_permission.assign(mock_actor, role.id, perm.id)
                
        domain_service.accounts.account_role.assign_role(mock_actor, acc.id, role.id)
        
        cred = domain_service.accounts.credential.set_credentials(acc.id, f"admin_{unique_suffix}", f"admin_{unique_suffix}@store.local", "password").data
    from flask_jwt_extended import create_access_token
    token = create_access_token(identity=str(acc.id))
    return {"Authorization": f"Bearer {token}"}

def test_get_movement_api(client, inventory_superuser_headers, stock_movement):
    res = client.get(f"/api/v1/inventory/movements/{stock_movement.id}", headers=inventory_superuser_headers)
    assert res.status_code == 200, res.get_data(as_text=True)
    assert res.get_json()["data"]["id"] == str(stock_movement.id)

def test_list_movements_api(client, inventory_superuser_headers, stock_movement):
    res = client.get("/api/v1/inventory/movements", headers=inventory_superuser_headers)
    assert res.status_code == 200
    assert res.get_json()["meta"]["total"] >= 1
