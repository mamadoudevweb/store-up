import uuid

import pytest

from flask_jwt_extended import create_access_token

from src.domains.rbac.repositories.filters import PermissionFilter
from src.domains.rbac.entities import Permission
from src.domains.stock.entities import StockItem
from tests.conftest import MockActor
from src.domains.stock.entities.enums import StockMovementReason, ReferenceType


@pytest.fixture
def variant_id():
    return uuid.uuid4()

@pytest.fixture
def stock_item(app, uow_factory, variant_id):
    with app.app_context():
        item = StockItem.create(variant_id=variant_id)
        with uow_factory() as uow:
            item = uow.stock_items.add(item)
            uow.commit()
            
        return item

@pytest.fixture
def stock_superuser_headers(app, uow_factory):
    with app.app_context():
        domain_service = app.extensions["domain_service"]
        mock_actor = MockActor({"*"})
        unique_suffix = uuid.uuid4().hex[:8]
        
        acc = domain_service.accounts.account.create_account("Admin", "Stock").data
        role = domain_service.rbac.role.create_role(mock_actor, f"stock_admin_{unique_suffix}", "Stock Admin").data
        
        perms_to_create = [
            ("stock:stock_item", "read"),
            ("stock:stock_item", "update"),
            ("stock:stock_movement", "read"),
            ("stock:stock_movement", "update"),
        ]
        
        for resource, action in perms_to_create:
            perm_id = None
            with uow_factory() as uow:
                perm = uow.permissions.get(PermissionFilter(resource=resource, action=action))
                if not perm:
                    perm = Permission(resource=resource, action=action, description="Full access")
                    perm = uow.permissions.add(perm)
                    uow.commit()
                perm_id = perm.id
            domain_service.rbac.role_permission.assign(mock_actor, role.id, perm_id)
                
        domain_service.accounts.account_role.assign_role(mock_actor, acc.id, role.id)
        
        cred = domain_service.accounts.credential.set_credentials(acc.id, f"admin_{unique_suffix}", f"admin_{unique_suffix}@store.local", "password").data
        token = create_access_token(identity=str(acc.id))
    return {"Authorization": f"Bearer {token}"}

def test_get_stock_item_api(client, stock_superuser_headers, stock_item):
    res = client.get(f"/api/v1/stock/items/{stock_item.variant_id}", headers=stock_superuser_headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["id"] == str(stock_item.id)

def test_list_stock_items_api(client, stock_superuser_headers, stock_item):
    res = client.get("/api/v1/stock/items", headers=stock_superuser_headers)
    assert res.status_code == 200
    assert res.get_json()["meta"]["total"] >= 1

def test_set_low_stock_threshold_api(client, stock_superuser_headers, stock_item, variant_id):
    res = client.put(
        f"/api/v1/stock/items/{variant_id}/threshold",
        json={"threshold": 20},
        headers=stock_superuser_headers
    )
    assert res.status_code == 200
    assert res.get_json()["data"]["low_stock_threshold"] == 20

def test_adjust_stock_api(client, stock_superuser_headers, stock_item, variant_id):
    res = client.post(
        f"/api/v1/stock/items/{variant_id}/adjust",
        json={"quantity_change": 100, "reason": StockMovementReason.RESTOCK.value, "reference_type": ReferenceType.PURCHASE_ORDER.value},
        headers=stock_superuser_headers
    )
    assert res.status_code == 200
    assert res.get_json()["data"]["quantity_on_hand"] == 100

def test_reserve_stock_api(client, stock_superuser_headers, stock_item, variant_id):
    client.post(
        f"/api/v1/stock/items/{variant_id}/adjust",
        json={"quantity_change": 100, "reason": StockMovementReason.RESTOCK.value, "reference_type": ReferenceType.PURCHASE_ORDER.value},
        headers=stock_superuser_headers
    )
    res = client.post(
        f"/api/v1/stock/items/{variant_id}/reserve",
        json={"quantity": 10, "reference_type": ReferenceType.SALE.value},
        headers=stock_superuser_headers
    )
    assert res.status_code == 200
    assert res.get_json()["data"]["quantity_reserved"] == 10

def test_release_stock_api(client, stock_superuser_headers, stock_item, variant_id):
    client.post(
        f"/api/v1/stock/items/{variant_id}/adjust",
        json={"quantity_change": 100, "reason": StockMovementReason.RESTOCK.value, "reference_type": ReferenceType.PURCHASE_ORDER.value},
        headers=stock_superuser_headers
    )
    client.post(
        f"/api/v1/stock/items/{variant_id}/reserve",
        json={"quantity": 20, "reference_type": ReferenceType.SALE.value},
        headers=stock_superuser_headers
    )
    res = client.post(
        f"/api/v1/stock/items/{variant_id}/release",
        json={"quantity": 5, "reference_type": ReferenceType.SALE.value},
        headers=stock_superuser_headers
    )
    assert res.status_code == 200
    assert res.get_json()["data"]["quantity_reserved"] == 15

def test_ship_stock_api(client, stock_superuser_headers, stock_item, variant_id):
    client.post(
        f"/api/v1/stock/items/{variant_id}/adjust",
        json={"quantity_change": 100, "reason": StockMovementReason.RESTOCK.value, "reference_type": ReferenceType.PURCHASE_ORDER.value},
        headers=stock_superuser_headers
    )
    client.post(
        f"/api/v1/stock/items/{variant_id}/reserve",
        json={"quantity": 20, "reference_type": ReferenceType.SALE.value},
        headers=stock_superuser_headers
    )
    res = client.post(
        f"/api/v1/stock/items/{variant_id}/ship",
        json={"quantity": 10, "reference_type": ReferenceType.SALE.value},
        headers=stock_superuser_headers
    )
    assert res.status_code == 200
    assert res.get_json()["data"]["quantity_on_hand"] == 90
    assert res.get_json()["data"]["quantity_reserved"] == 10
