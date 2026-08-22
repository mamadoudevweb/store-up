import uuid
from datetime import datetime

import pytest

from src.domains.inventory.entities import InventoryItem, StockMovement
from src.domains.inventory.exceptions import (
    InsufficientReservedStockError,
    InsufficientStockError,
    InventoryItemNotFound,
)
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
def inventory_item(uow_factory, product_id):
    item = InventoryItem(product_id=product_id)
    with uow_factory() as uow:
        item = uow.inventory_items.add(item)
        uow.commit()
    return item

def test_get_inventory_item(inventory_service, mock_actor, inventory_item):
    res = inventory_service.inventory_item.get_inventory_item(mock_actor, inventory_item.id)
    assert res.success
    assert res.data.id == inventory_item.id

def test_get_inventory_item_not_found(inventory_service, mock_actor):
    with pytest.raises(InventoryItemNotFound):
        inventory_service.inventory_item.get_inventory_item(mock_actor, uuid.uuid4())

def test_list_inventory_items(inventory_service, mock_actor, inventory_item):
    from src.domains.inventory.repositories.filters import InventoryItemFilter
    res = inventory_service.inventory_item.list_inventory_items(mock_actor, InventoryItemFilter())
    assert res.success
    assert res.data.total >= 1

def test_set_low_stock_threshold(inventory_service, mock_actor, inventory_item, product_id):
    res = inventory_service.inventory_item.set_low_stock_threshold(mock_actor, product_id, 10)
    assert res.success
    assert res.data.low_stock_threshold == 10

def test_set_low_stock_threshold_not_found(inventory_service, mock_actor):
    with pytest.raises(InventoryItemNotFound):
        inventory_service.inventory_item.set_low_stock_threshold(mock_actor, uuid.uuid4(), 10)

def test_adjust_stock(inventory_service, mock_actor, inventory_item, product_id):
    res = inventory_service.inventory_item.adjust_stock(mock_actor, product_id, 50, "INITIAL_STOCK")
    assert res.success
    assert res.data.quantity_on_hand == 50
    
    # Negative adjust stock
    res = inventory_service.inventory_item.adjust_stock(mock_actor, product_id, -10, "DAMAGE")
    assert res.success
    assert res.data.quantity_on_hand == 40

def test_adjust_stock_not_found(inventory_service, mock_actor):
    with pytest.raises(InventoryItemNotFound):
        inventory_service.inventory_item.adjust_stock(mock_actor, uuid.uuid4(), 50, "INITIAL_STOCK")

def test_adjust_stock_insufficient(inventory_service, mock_actor, inventory_item, product_id):
    with pytest.raises(InsufficientStockError):
        inventory_service.inventory_item.adjust_stock(mock_actor, product_id, -10, "DAMAGE")

def test_reserve_stock(inventory_service, mock_actor, inventory_item, product_id):
    inventory_service.inventory_item.adjust_stock(mock_actor, product_id, 50, "INITIAL_STOCK")
    res = inventory_service.inventory_item.reserve_stock(mock_actor, product_id, 10)
    assert res.success
    assert res.data.quantity_on_hand == 50
    assert res.data.quantity_reserved == 10
    assert res.data.available_quantity == 40

def test_reserve_stock_not_found(inventory_service, mock_actor):
    with pytest.raises(InventoryItemNotFound):
        inventory_service.inventory_item.reserve_stock(mock_actor, uuid.uuid4(), 10)

def test_reserve_stock_insufficient(inventory_service, mock_actor, inventory_item, product_id):
    inventory_service.inventory_item.adjust_stock(mock_actor, product_id, 5, "INITIAL_STOCK")
    with pytest.raises(InsufficientStockError):
        inventory_service.inventory_item.reserve_stock(mock_actor, product_id, 10)

def test_release_stock(inventory_service, mock_actor, inventory_item, product_id):
    inventory_service.inventory_item.adjust_stock(mock_actor, product_id, 50, "INITIAL_STOCK")
    inventory_service.inventory_item.reserve_stock(mock_actor, product_id, 20)
    
    res = inventory_service.inventory_item.release_stock(mock_actor, product_id, 10)
    assert res.success
    assert res.data.quantity_reserved == 10
    assert res.data.available_quantity == 40

def test_release_stock_not_found(inventory_service, mock_actor):
    with pytest.raises(InventoryItemNotFound):
        inventory_service.inventory_item.release_stock(mock_actor, uuid.uuid4(), 10)

def test_release_stock_insufficient(inventory_service, mock_actor, inventory_item, product_id):
    inventory_service.inventory_item.adjust_stock(mock_actor, product_id, 50, "INITIAL_STOCK")
    inventory_service.inventory_item.reserve_stock(mock_actor, product_id, 5)
    with pytest.raises(InsufficientReservedStockError):
        inventory_service.inventory_item.release_stock(mock_actor, product_id, 10)

def test_ship_stock(inventory_service, mock_actor, inventory_item, product_id):
    inventory_service.inventory_item.adjust_stock(mock_actor, product_id, 50, "INITIAL_STOCK")
    inventory_service.inventory_item.reserve_stock(mock_actor, product_id, 20)
    
    res = inventory_service.inventory_item.ship_stock(mock_actor, product_id, 15)
    assert res.success
    assert res.data.quantity_on_hand == 35
    assert res.data.quantity_reserved == 5
    assert res.data.available_quantity == 30

def test_ship_stock_not_found(inventory_service, mock_actor):
    with pytest.raises(InventoryItemNotFound):
        inventory_service.inventory_item.ship_stock(mock_actor, uuid.uuid4(), 10)

def test_ship_stock_insufficient(inventory_service, mock_actor, inventory_item, product_id):
    inventory_service.inventory_item.adjust_stock(mock_actor, product_id, 50, "INITIAL_STOCK")
    inventory_service.inventory_item.reserve_stock(mock_actor, product_id, 5)
    with pytest.raises(InsufficientReservedStockError):
        inventory_service.inventory_item.ship_stock(mock_actor, product_id, 10)
