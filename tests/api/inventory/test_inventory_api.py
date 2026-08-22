import uuid

import pytest

@pytest.fixture
def product_id():
    return uuid.uuid4()

@pytest.fixture
def inventory_item(app, uow_factory, product_id):
    with app.app_context():
        domain_service = app.extensions["domain_service"]
        from tests.conftest import MockActor
        mock_actor = MockActor({"*"})
        
        # Since domain_service doesn't have a direct create_inventory_item, we just adjust stock on a new product to create it?
        # Actually InventoryItem is automatically created if it doesn't exist? Wait, no. The service says InventoryItemNotFound.
        # How is inventory item created? Through events or manual?
        # Let's bypass and create directly in DB.
        from src.domains.inventory.entities import InventoryItem
        item = InventoryItem(product_id=product_id)
        with uow_factory() as uow:
            item = uow.inventory_items.add(item)
            uow.commit()
            
        return item

@pytest.fixture
def inventory_superuser_headers(app, uow_factory):
    with app.app_context():
        domain_service = app.extensions["domain_service"]
        from tests.conftest import MockActor
        mock_actor = MockActor({"*"})
        unique_suffix = uuid.uuid4().hex[:8]
        
        acc = domain_service.accounts.account.create_account("Admin", "Inventory").data
        role = domain_service.rbac.role.create_role(mock_actor, f"inventory_admin_{unique_suffix}", "Inventory Admin").data
        
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

def test_get_inventory_item_api(client, inventory_superuser_headers, inventory_item):
    res = client.get(f"/api/v1/inventory/items/{inventory_item.product_id}", headers=inventory_superuser_headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["id"] == str(inventory_item.id)

def test_list_inventory_items_api(client, inventory_superuser_headers, inventory_item):
    res = client.get("/api/v1/inventory/items", headers=inventory_superuser_headers)
    assert res.status_code == 200
    assert res.get_json()["meta"]["total"] >= 1

def test_set_low_stock_threshold_api(client, inventory_superuser_headers, inventory_item, product_id):
    res = client.put(
        f"/api/v1/inventory/items/{product_id}/threshold",
        json={"threshold": 20},
        headers=inventory_superuser_headers
    )
    assert res.status_code == 200
    assert res.get_json()["data"]["low_stock_threshold"] == 20

def test_adjust_stock_api(client, inventory_superuser_headers, inventory_item, product_id):
    res = client.post(
        f"/api/v1/inventory/items/{product_id}/adjust",
        json={"quantity_change": 100, "reason": "RESTOCK"},
        headers=inventory_superuser_headers
    )
    assert res.status_code == 200
    assert res.get_json()["data"]["quantity_on_hand"] == 100

def test_reserve_stock_api(client, inventory_superuser_headers, inventory_item, product_id):
    client.post(
        f"/api/v1/inventory/items/{product_id}/adjust",
        json={"quantity_change": 100, "reason": "RESTOCK"},
        headers=inventory_superuser_headers
    )
    res = client.post(
        f"/api/v1/inventory/items/{product_id}/reserve",
        json={"quantity": 10},
        headers=inventory_superuser_headers
    )
    assert res.status_code == 200
    assert res.get_json()["data"]["quantity_reserved"] == 10

def test_release_stock_api(client, inventory_superuser_headers, inventory_item, product_id):
    client.post(
        f"/api/v1/inventory/items/{product_id}/adjust",
        json={"quantity_change": 100, "reason": "RESTOCK"},
        headers=inventory_superuser_headers
    )
    client.post(
        f"/api/v1/inventory/items/{product_id}/reserve",
        json={"quantity": 20},
        headers=inventory_superuser_headers
    )
    res = client.post(
        f"/api/v1/inventory/items/{product_id}/release",
        json={"quantity": 5},
        headers=inventory_superuser_headers
    )
    assert res.status_code == 200
    assert res.get_json()["data"]["quantity_reserved"] == 15

def test_ship_stock_api(client, inventory_superuser_headers, inventory_item, product_id):
    client.post(
        f"/api/v1/inventory/items/{product_id}/adjust",
        json={"quantity_change": 100, "reason": "RESTOCK"},
        headers=inventory_superuser_headers
    )
    client.post(
        f"/api/v1/inventory/items/{product_id}/reserve",
        json={"quantity": 20},
        headers=inventory_superuser_headers
    )
    res = client.post(
        f"/api/v1/inventory/items/{product_id}/ship",
        json={"quantity": 10},
        headers=inventory_superuser_headers
    )
    assert res.status_code == 200
    assert res.get_json()["data"]["quantity_on_hand"] == 90
    assert res.get_json()["data"]["quantity_reserved"] == 10
