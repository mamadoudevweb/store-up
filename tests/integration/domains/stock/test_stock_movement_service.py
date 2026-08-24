import uuid

import pytest

from src.domains.stock.entities import StockMovement
from src.domains.stock.entities.enums import StockMovementReason, ReferenceType
from src.domains.stock.exceptions import StockMovementNotFound
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
def stock_item_id():
    return uuid.uuid4()


@pytest.fixture
def stock_movement(uow_factory, stock_item_id):
    movement = StockMovement.create(
        stock_item_id=stock_item_id,
        quantity_change=10,
        reason=StockMovementReason.RESTOCK,
        reference_type=ReferenceType.PURCHASE_ORDER,
        reference_id="TEST-123",
    )
    with uow_factory() as uow:
        movement = uow.stock_movements.add(movement)
        uow.commit()
    return movement


def test_get_movement(stock_service, mock_actor, stock_movement):
    res = stock_service.movement.get_movement(mock_actor, stock_movement.id)
    assert res.success
    assert res.data.id == stock_movement.id


def test_get_movement_not_found(stock_service, mock_actor):
    with pytest.raises(StockMovementNotFound):
        stock_service.movement.get_movement(mock_actor, uuid.uuid4())


def test_list_movements(stock_service, mock_actor, stock_movement):
    from src.domains.stock.repositories.filters import StockMovementFilter

    res = stock_service.movement.list_movements(mock_actor, StockMovementFilter())
    assert res.success
    assert res.data.total >= 1
