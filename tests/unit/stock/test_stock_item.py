import uuid
import pytest
from src.domains.stock.entities import StockItem
from src.domains.stock.entities.enums import ReferenceType
from src.domains.stock.events import StockAdjusted, StockReserved, StockShipped, StockReleased, LowStockAlert, OutOfStock

def test_stock_item_adjust_stock():
    item = StockItem.create(variant_id=uuid.uuid4(), low_stock_threshold=5)
    assert item.quantity_on_hand == 0
    assert item.available_quantity == 0
    
    item.adjust_stock(10)
    assert item.quantity_on_hand == 10
    assert item.available_quantity == 10
    assert isinstance(item._events[-1], StockAdjusted)

def test_stock_item_reserve_and_ship():
    item = StockItem.create(variant_id=uuid.uuid4())
    item.adjust_stock(10)
    
    item.reserve_stock(3, ReferenceType.SALE, "order-1")
    assert item.quantity_reserved == 3
    assert item.available_quantity == 7
    assert isinstance(item._events[-1], StockReserved)
    
    item.ship_stock(3, ReferenceType.SALE, "order-1")
    assert item.quantity_on_hand == 7
    assert item.quantity_reserved == 0
    assert item.available_quantity == 7
    assert isinstance(item._events[-1], StockShipped)

def test_stock_item_insufficient_stock():
    item = StockItem.create(variant_id=uuid.uuid4())
    item.adjust_stock(5)
    
    with pytest.raises(ValueError):
        item.reserve_stock(10, ReferenceType.SALE)
