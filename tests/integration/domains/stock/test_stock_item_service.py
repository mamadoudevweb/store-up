import uuid
from datetime import datetime

import pytest

from src.domains.stock.entities import StockItem, StockMovement
from src.domains.stock.entities.enums import StockMovementReason, ReferenceType
from src.domains.stock.exceptions import (
    InsufficientReservedStockError,
    InsufficientStockError,
    StockItemNotFound,
)
from src.domains.stock.services import StockDomainService
from src.domains.stock.services.stock_item_service import StockItemService
from src.domains.stock.services.stock_movement_service import StockMovementService

@pytest.fixture
def stock_service(uow_factory):
    return StockDomainService(
        item=StockItemService(uow_factory),
        movement=StockMovementService(uow_factory)
    )


@pytest.fixture
def variant_id():
    return uuid.uuid4()

@pytest.fixture
def stock_item(uow_factory, variant_id):
    item = StockItem.create(variant_id=variant_id)
    with uow_factory() as uow:
        item = uow.stock_items.add(item)
        uow.commit()
    return item

def test_get_stock_item(stock_service, mock_actor, stock_item):
    res = stock_service.item.get_stock_item(mock_actor, stock_item.id)
    assert res.success
    assert res.data.id == stock_item.id

def test_get_stock_item_not_found(stock_service, mock_actor):
    with pytest.raises(StockItemNotFound):
        stock_service.item.get_stock_item(mock_actor, uuid.uuid4())

def test_list_stock_items(stock_service, mock_actor, stock_item):
    from src.domains.stock.repositories.filters import StockItemFilter
    res = stock_service.item.list_stock_items(mock_actor, StockItemFilter())
    assert res.success
    assert res.data.total >= 1

def test_set_low_stock_threshold(stock_service, mock_actor, stock_item, variant_id):
    res = stock_service.item.set_low_stock_threshold(mock_actor, variant_id, 10)
    assert res.success
    assert res.data.low_stock_threshold == 10

def test_set_low_stock_threshold_not_found(stock_service, mock_actor):
    with pytest.raises(StockItemNotFound):
        stock_service.item.set_low_stock_threshold(mock_actor, uuid.uuid4(), 10)

def test_adjust_stock(stock_service, mock_actor, stock_item, variant_id):
    res = stock_service.item.adjust_stock(
        mock_actor, 
        variant_id, 
        50, 
        StockMovementReason.MANUAL_ADJUSTMENT,
        ReferenceType.MANUAL_ADJUSTMENT
    )
    assert res.success
    assert res.data.quantity_on_hand == 50
    
    # Negative adjust stock
    res = stock_service.item.adjust_stock(
        mock_actor, 
        variant_id, 
        -10, 
        StockMovementReason.DAMAGE,
        ReferenceType.MANUAL_ADJUSTMENT
    )
    assert res.success
    assert res.data.quantity_on_hand == 40

def test_adjust_stock_not_found(stock_service, mock_actor):
    with pytest.raises(StockItemNotFound):
        stock_service.item.adjust_stock(
            mock_actor, 
            uuid.uuid4(), 
            50, 
            StockMovementReason.MANUAL_ADJUSTMENT,
            ReferenceType.MANUAL_ADJUSTMENT
        )

def test_adjust_stock_insufficient(stock_service, mock_actor, stock_item, variant_id):
    with pytest.raises(InsufficientStockError):
        stock_service.item.adjust_stock(
            mock_actor, 
            variant_id, 
            -10, 
            StockMovementReason.DAMAGE,
            ReferenceType.MANUAL_ADJUSTMENT
        )

def test_reserve_stock(stock_service, mock_actor, stock_item, variant_id):
    stock_service.item.adjust_stock(
        mock_actor, 
        variant_id, 
        50, 
        StockMovementReason.RESTOCK,
        ReferenceType.PURCHASE_ORDER
    )
    res = stock_service.item.reserve_stock(
        mock_actor, 
        variant_id, 
        10,
        ReferenceType.SALE
    )
    assert res.success
    assert res.data.quantity_on_hand == 50
    assert res.data.quantity_reserved == 10
    assert res.data.available_quantity == 40

def test_reserve_stock_not_found(stock_service, mock_actor):
    with pytest.raises(StockItemNotFound):
        stock_service.item.reserve_stock(
            mock_actor, 
            uuid.uuid4(), 
            10,
            ReferenceType.SALE
        )

def test_reserve_stock_insufficient(stock_service, mock_actor, stock_item, variant_id):
    stock_service.item.adjust_stock(
        mock_actor, 
        variant_id, 
        5, 
        StockMovementReason.RESTOCK,
        ReferenceType.PURCHASE_ORDER
    )
    with pytest.raises(InsufficientStockError):
        stock_service.item.reserve_stock(
            mock_actor, 
            variant_id, 
            10,
            ReferenceType.SALE
        )

def test_release_stock(stock_service, mock_actor, stock_item, variant_id):
    stock_service.item.adjust_stock(
        mock_actor, 
        variant_id, 
        50, 
        StockMovementReason.RESTOCK,
        ReferenceType.PURCHASE_ORDER
    )
    stock_service.item.reserve_stock(
        mock_actor, 
        variant_id, 
        20,
        ReferenceType.SALE
    )
    
    res = stock_service.item.release_stock(
        mock_actor, 
        variant_id, 
        10,
        ReferenceType.SALE
    )
    assert res.success
    assert res.data.quantity_reserved == 10
    assert res.data.available_quantity == 40

def test_release_stock_not_found(stock_service, mock_actor):
    with pytest.raises(StockItemNotFound):
        stock_service.item.release_stock(
            mock_actor, 
            uuid.uuid4(), 
            10,
            ReferenceType.SALE
        )

def test_release_stock_insufficient(stock_service, mock_actor, stock_item, variant_id):
    stock_service.item.adjust_stock(
        mock_actor, 
        variant_id, 
        50, 
        StockMovementReason.RESTOCK,
        ReferenceType.PURCHASE_ORDER
    )
    stock_service.item.reserve_stock(
        mock_actor, 
        variant_id, 
        5,
        ReferenceType.SALE
    )
    with pytest.raises(InsufficientReservedStockError):
        stock_service.item.release_stock(
            mock_actor, 
            variant_id, 
            10,
            ReferenceType.SALE
        )

def test_ship_stock(stock_service, mock_actor, stock_item, variant_id):
    stock_service.item.adjust_stock(
        mock_actor, 
        variant_id, 
        50, 
        StockMovementReason.RESTOCK,
        ReferenceType.PURCHASE_ORDER
    )
    stock_service.item.reserve_stock(
        mock_actor, 
        variant_id, 
        20,
        ReferenceType.SALE
    )
    
    res = stock_service.item.ship_stock(
        mock_actor, 
        variant_id, 
        15,
        ReferenceType.SALE
    )
    assert res.success
    assert res.data.quantity_on_hand == 35
    assert res.data.quantity_reserved == 5
    assert res.data.available_quantity == 30

def test_ship_stock_not_found(stock_service, mock_actor):
    with pytest.raises(StockItemNotFound):
        stock_service.item.ship_stock(
            mock_actor, 
            uuid.uuid4(), 
            10,
            ReferenceType.SALE
        )

def test_ship_stock_insufficient(stock_service, mock_actor, stock_item, variant_id):
    stock_service.item.adjust_stock(
        mock_actor, 
        variant_id, 
        50, 
        StockMovementReason.RESTOCK,
        ReferenceType.PURCHASE_ORDER
    )
    stock_service.item.reserve_stock(
        mock_actor, 
        variant_id, 
        5,
        ReferenceType.SALE
    )
    with pytest.raises(InsufficientReservedStockError):
        stock_service.item.ship_stock(
            mock_actor, 
            variant_id, 
            10,
            ReferenceType.SALE
        )
