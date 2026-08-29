import uuid

import pytest

from flask_jwt_extended import create_access_token

from src.domains.rbac.repositories.filters import PermissionFilter
from src.domains.rbac.entities import Permission
from src.domains.stock.entities import StockMovement
from tests.conftest import MockActor
from src.domains.stock.entities.enums import StockMovementReason, ReferenceType


@pytest.fixture
def stock_item_id():
    return uuid.uuid4()

@pytest.fixture
def stock_movement(app, uow_factory, stock_item_id):
    with app.app_context():
        movement = StockMovement.create(
            stock_item_id=stock_item_id,
            quantity_change=10,
            reason=StockMovementReason.RESTOCK,
            reference_type=ReferenceType.PURCHASE_ORDER,
        )
        with uow_factory() as uow:
            movement = uow.stock_movements.add(movement)
            uow.commit()
            
        return movement

@pytest.fixture
def stock_superuser_headers(app, uow_factory):
    with app.app_context():
        domain_service = app.extensions["domain_service"]
        mock_actor = MockActor({"*"})
        unique_suffix = uuid.uuid4().hex[:8]
        
        acc = domain_service.accounts.account.create_account("Admin", "Stock").data
        role = domain_service.rbac.role.create_role(mock_actor, f"stk_admin_{unique_suffix}", "Stock Admin").data
        
        # Manually create permissions using UOW since service doesn't have get_by_name
        perms_to_create = [
            ("stock:stock_item", "read"),
            ("stock:stock_item", "update"),
            ("stock:stock_movement", "read"),
            ("stock:stock_movement", "update"),
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
        token = create_access_token(identity=str(acc.id))
    return {"Authorization": f"Bearer {token}"}

def test_get_movement_api(client, stock_superuser_headers, stock_movement):
    res = client.get(f"/api/v1/stock/movements/{stock_movement.id}", headers=stock_superuser_headers)
    assert res.status_code == 200, res.get_data(as_text=True)
    assert res.get_json()["data"]["id"] == str(stock_movement.id)

def test_list_movements_api(client, stock_superuser_headers, stock_movement):
    res = client.get("/api/v1/stock/movements", headers=stock_superuser_headers)
    assert res.status_code == 200
    assert res.get_json()["meta"]["total"] >= 1
