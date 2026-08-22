import uuid

import pytest

from src.domains.inventory.entities import StockMovement
from src.domains.inventory.exceptions import StockMovementNotFound
from src.domains.inventory.services import InventoryDomainService
from src.domains.inventory.services.inventory_item_service import InventoryItemService
from src.domains.inventory.services.stock_movement_service import StockMovementService

@pytest.fixture
def inventory_service(uow_factory):
    return InventoryDomainService(
        inventory_item=InventoryItemService(uow_factory),
        stock_movement=StockMovementService(uow_factory)
    )



@pytest.fixture
def product_id():
    return uuid.uuid4()


@pytest.fixture
def stock_movement(uow_factory, product_id):
    movement = StockMovement.create(
        product_id=product_id,
        quantity_change=10,
        reason="TEST",
        reference_id="TEST-123",
    )
    with uow_factory() as uow:
        movement = uow.stock_movements.add(movement)
        uow.commit()
    return movement


def test_get_movement(inventory_service, mock_actor, stock_movement):
    res = inventory_service.stock_movement.get_movement(mock_actor, stock_movement.id)
    assert res.success
    assert res.data.id == stock_movement.id


def test_get_movement_not_found(inventory_service, mock_actor):
    with pytest.raises(StockMovementNotFound):
        inventory_service.stock_movement.get_movement(mock_actor, uuid.uuid4())


def test_list_movements(inventory_service, mock_actor, stock_movement):
    from src.domains.inventory.repositories.filters import StockMovementFilter

    res = inventory_service.stock_movement.list_movements(mock_actor, StockMovementFilter())
    assert res.success
    assert res.data.total >= 1
