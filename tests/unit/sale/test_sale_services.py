import uuid
import pytest
from unittest.mock import MagicMock

from src.domains.sale.services.sale_service import SaleService
from src.domains.sale.services.refund_service import RefundService
from src.domains.sale.exceptions import (
    InsufficientStockError,
    RefundNotFoundError,
    RefundQuantityExceededError,
    SaleLineNotFoundError,
    SaleNotFoundError,
)


@pytest.fixture
def uow_mock():
    """
    Create a mock unit of work configured for context-manager usage.
    
    Returns:
    	MagicMock: A mock whose context manager entry returns itself.
    """
    uow = MagicMock()
    uow.__enter__.return_value = uow
    uow.__exit__.return_value = None
    return uow


@pytest.fixture
def uow_factory(uow_mock):
    """Create a factory that returns the provided unit-of-work mock.
    
    Parameters:
    	uow_mock: The unit-of-work mock to return.
    
    Returns:
    	A callable that returns the provided unit-of-work mock.
    """
    return lambda: uow_mock


@pytest.fixture
def account_mock():
    """Create a mocked account whose permission checks succeed.
    
    Returns:
        MagicMock: A mocked account configured to grant requested permissions.
    """
    account = MagicMock()
    account.has_permission.return_value = True
    return account


def test_checkout_service_success(uow_mock, uow_factory, account_mock):
    uow_mock.stock_items.atomic_reserve.return_value = True
    
    service = SaleService(uow_factory)
    
    result = service.checkout(
        account=account_mock,
        seller_account_id=uuid.uuid4(),
        payment_method_id=uuid.uuid4(),
        lines_data=[
            {
                "variant_id": uuid.uuid4(),
                "quantity": 2,
                "unit_price": 100,
                "discount": 0
            }
        ]
    )
    
    sale = result.data
    from src.domains.sale.entities.enums import SaleStatus
    assert sale.status == SaleStatus.PENDING
    uow_mock.stock_items.atomic_reserve.assert_called_once()
    uow_mock.sales.add.assert_called_once_with(sale)
    uow_mock.track.assert_called_once_with(sale)
    uow_mock.commit.assert_called_once()


def test_checkout_service_insufficient_stock(uow_mock, uow_factory, account_mock):
    uow_mock.stock_items.atomic_reserve.return_value = False
    
    service = SaleService(uow_factory)
    
    with pytest.raises(InsufficientStockError):
        service.checkout(
            account=account_mock,
            seller_account_id=uuid.uuid4(),
            payment_method_id=uuid.uuid4(),
            lines_data=[
                {
                    "variant_id": uuid.uuid4(),
                    "quantity": 2,
                    "unit_price": 100,
                    "discount": 0
                }
            ]
        )
        
    uow_mock.rollback.assert_called_once()
    uow_mock.sales.add.assert_not_called()


def test_complete_sale(uow_mock, uow_factory, account_mock):
    sale = MagicMock()
    uow_mock.sales.get.return_value = sale
    
    service = SaleService(uow_factory)
    result = service.complete_sale(account=account_mock, sale_id=uuid.uuid4())
    
    sale.mark_completed.assert_called_once()
    uow_mock.sales.update.assert_called_once_with(sale)
    uow_mock.track.assert_called_once_with(sale)
    uow_mock.commit.assert_called_once()
    assert result.data == sale


def test_request_refund(uow_mock, uow_factory, account_mock):
    sale = MagicMock()
    
    sale_line = MagicMock()
    sale_line.id = uuid.uuid4()
    sale_line.quantity = 5
    sale_line.refunded_quantity = 0
    sale_line.unit_price = 100
    sale_line.discount = 10
    sale.lines = [sale_line]
    sale.subtotal = 450
    sale.discount = 45
    
    uow_mock.sales.get.return_value = sale
    
    service = RefundService(uow_factory)
    
    sale_id = uuid.uuid4()
    
    result = service.request_refund(
        account=account_mock,
        sale_id=sale_id,
        processed_by=uuid.uuid4(),
        reason="Defective",
        lines_data=[
            {
                "sale_line_id": sale_line.id,
                "quantity": 2
            }
        ]
    )
    
    refund = result.data
    assert refund.reason == "Defective"
    assert refund.lines[0].quantity == 2
    
    from src.domains.sale.events import RefundRequested
    assert len(refund._events) == 1
    event = refund._events[0]
    assert isinstance(event, RefundRequested)
    
    # Expected amount calculation:
    # 2 units * (100 - 10) = 180
    # allocated discount = int((180 / 450) * 45) = 18
    # amount = 180 - 18 = 162
    assert event.amount == 162
    assert event.sale_id == sale_id
    assert event.lines_data == [{"sale_line_id": sale_line.id, "quantity": 2}]
    
    uow_mock.refunds.add.assert_called_once_with(refund)


def test_request_refund_duplicate_lines_exceed_quantity(uow_mock, uow_factory, account_mock):
    sale = MagicMock()
    
    sale_line = MagicMock()
    sale_line.id = uuid.uuid4()
    sale_line.quantity = 5
    sale_line.refunded_quantity = 0
    sale_line.unit_price = 100
    sale_line.discount = 10
    sale.lines = [sale_line]
    sale.subtotal = 450
    sale.discount = 45
    
    uow_mock.sales.get.return_value = sale
    
    service = RefundService(uow_factory)
    
    from src.domains.sale.exceptions import RefundQuantityExceededError
    with pytest.raises(RefundQuantityExceededError):
        service.request_refund(
            account=account_mock,
            sale_id=uuid.uuid4(),
            processed_by=uuid.uuid4(),
            reason="Duplicate lines",
            lines_data=[
                {
                    "sale_line_id": sale_line.id,
                    "quantity": 3
                },
                {
                    "sale_line_id": sale_line.id,
                    "quantity": 3
                }
            ]
        )


def test_request_refund_partial_cumulative(uow_mock, uow_factory, account_mock):
    sale = MagicMock()
    
    sale_line = MagicMock()
    sale_line.id = uuid.uuid4()
    sale_line.quantity = 5
    sale_line.refunded_quantity = 2  # Already refunded 2
    sale_line.unit_price = 100
    sale_line.discount = 10
    sale.lines = [sale_line]
    sale.subtotal = 450
    sale.discount = 45
    
    uow_mock.sales.get.return_value = sale
    
    service = RefundService(uow_factory)
    
    result = service.request_refund(
        account=account_mock,
        sale_id=uuid.uuid4(),
        processed_by=uuid.uuid4(),
        reason="Return remaining",
        lines_data=[
            {
                "sale_line_id": sale_line.id,
                "quantity": 3
            }
        ]
    )
    
    refund = result.data
    event = refund._events[0]
    
    # Before amount: 2 * 90 = 180. allocated = int(180/450 * 45) = 18. amount = 162
    # After amount: 5 * 90 = 450. allocated = int(450/450 * 45) = 45. amount = 405
    # Expected current refund amount: 405 - 162 = 243
    assert event.amount == 243

def test_checkout_reserves_stock_in_variant_id_order(uow_mock, uow_factory, account_mock):
    uow_mock.stock_items.atomic_reserve.return_value = True

    variant_high = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
    variant_low = uuid.UUID("00000000-0000-0000-0000-000000000000")

    service = SaleService(uow_factory)
    service.checkout(
        account=account_mock,
        seller_account_id=uuid.uuid4(),
        payment_method_id=uuid.uuid4(),
        lines_data=[
            {"variant_id": variant_high, "quantity": 1, "unit_price": 10, "discount": 0},
            {"variant_id": variant_low, "quantity": 1, "unit_price": 10, "discount": 0},
        ],
    )

    calls = uow_mock.stock_items.atomic_reserve.call_args_list
    reserved_variant_ids = [call.args[0] for call in calls]
    assert reserved_variant_ids == [variant_low, variant_high]


def test_complete_sale_not_found(uow_mock, uow_factory, account_mock):
    uow_mock.sales.get.return_value = None

    service = SaleService(uow_factory)

    with pytest.raises(SaleNotFoundError):
        service.complete_sale(account=account_mock, sale_id=uuid.uuid4())

    uow_mock.sales.update.assert_not_called()


def test_fail_sale_marks_failed_and_releases_stock(uow_mock, uow_factory, account_mock):
    sale = MagicMock()
    line1 = MagicMock(variant_id=uuid.uuid4(), quantity=2)
    line2 = MagicMock(variant_id=uuid.uuid4(), quantity=1)
    sale.lines = [line1, line2]
    uow_mock.sales.get.return_value = sale

    service = SaleService(uow_factory)
    result = service.fail_sale(account=account_mock, sale_id=uuid.uuid4(), reason="Card declined")

    sale.mark_failed.assert_called_once_with("Card declined")
    assert uow_mock.stock_items.atomic_release.call_count == 2
    uow_mock.stock_items.atomic_release.assert_any_call(line1.variant_id, line1.quantity)
    uow_mock.stock_items.atomic_release.assert_any_call(line2.variant_id, line2.quantity)
    uow_mock.sales.update.assert_called_once_with(sale)
    uow_mock.commit.assert_called_once()
    assert result.data == sale


def test_fail_sale_not_found(uow_mock, uow_factory, account_mock):
    uow_mock.sales.get.return_value = None

    service = SaleService(uow_factory)

    with pytest.raises(SaleNotFoundError):
        service.fail_sale(account=account_mock, sale_id=uuid.uuid4(), reason="Card declined")

    uow_mock.stock_items.atomic_release.assert_not_called()


def test_request_refund_sale_not_found(uow_mock, uow_factory, account_mock):
    uow_mock.sales.get.return_value = None

    service = RefundService(uow_factory)

    with pytest.raises(SaleNotFoundError):
        service.request_refund(
            account=account_mock,
            sale_id=uuid.uuid4(),
            processed_by=uuid.uuid4(),
            reason="Defective",
            lines_data=[{"sale_line_id": uuid.uuid4(), "quantity": 1}],
        )


def test_request_refund_sale_line_not_found(uow_mock, uow_factory, account_mock):
    sale = MagicMock()
    sale.subtotal = 100
    sale.discount = 0
    sale.lines = []
    uow_mock.sales.get.return_value = sale

    service = RefundService(uow_factory)

    with pytest.raises(SaleLineNotFoundError):
        service.request_refund(
            account=account_mock,
            sale_id=uuid.uuid4(),
            processed_by=uuid.uuid4(),
            reason="Defective",
            lines_data=[{"sale_line_id": uuid.uuid4(), "quantity": 1}],
        )


def test_request_refund_quantity_exceeded(uow_mock, uow_factory, account_mock):
    sale = MagicMock()
    sale.subtotal = 100
    sale.discount = 0
    sale_line = MagicMock()
    sale_line.id = uuid.uuid4()
    sale_line.quantity = 2
    sale_line.refunded_quantity = 1
    sale.lines = [sale_line]
    uow_mock.sales.get.return_value = sale

    service = RefundService(uow_factory)

    with pytest.raises(RefundQuantityExceededError):
        service.request_refund(
            account=account_mock,
            sale_id=uuid.uuid4(),
            processed_by=uuid.uuid4(),
            reason="Too much",
            lines_data=[{"sale_line_id": sale_line.id, "quantity": 2}],
        )

    uow_mock.refunds.add.assert_not_called()


def test_complete_refund(uow_mock, uow_factory, account_mock):
    refund = MagicMock()
    uow_mock.refunds.get.return_value = refund

    service = RefundService(uow_factory)
    refund_id = uuid.uuid4()
    result = service.complete_refund(account=account_mock, refund_id=refund_id)

    refund.mark_processed.assert_called_once()
    uow_mock.refunds.update.assert_called_once_with(refund)
    uow_mock.commit.assert_called_once()
    assert result.data == refund


def test_complete_refund_not_found(uow_mock, uow_factory, account_mock):
    uow_mock.refunds.get.return_value = None

    service = RefundService(uow_factory)

    with pytest.raises(RefundNotFoundError):
        service.complete_refund(account=account_mock, refund_id=uuid.uuid4())

    uow_mock.refunds.update.assert_not_called()


def test_fail_refund(uow_mock, uow_factory, account_mock):
    refund = MagicMock()
    uow_mock.refunds.get.return_value = refund

    service = RefundService(uow_factory)
    refund_id = uuid.uuid4()
    result = service.fail_refund(account=account_mock, refund_id=refund_id)

    refund.mark_failed.assert_called_once()
    uow_mock.refunds.update.assert_called_once_with(refund)
    uow_mock.commit.assert_called_once()
    assert result.data == refund


def test_fail_refund_not_found(uow_mock, uow_factory, account_mock):
    uow_mock.refunds.get.return_value = None

    service = RefundService(uow_factory)

    with pytest.raises(RefundNotFoundError):
        service.fail_refund(account=account_mock, refund_id=uuid.uuid4())

    uow_mock.refunds.update.assert_not_called()


def test_sale_service_process_refund(uow_mock, uow_factory, account_mock):
    sale = MagicMock()
    
    sale_line = MagicMock()
    sale_line.id = uuid.uuid4()
    sale_line.quantity = 5
    sale_line.refunded_quantity = 0
    sale.lines = [sale_line]
    
    uow_mock.sales.get.return_value = sale
    
    service = SaleService(uow_factory)
    refund_id = uuid.uuid4()
    
    result = service.process_refund(
        account=account_mock,
        sale_id=uuid.uuid4(),
        refund_id=refund_id,
        lines_data=[
            {
                "sale_line_id": sale_line.id,
                "quantity": 2
            }
        ],
        amount=200
    )
    
    assert sale_line.refunded_quantity == 2
    sale.process_refund.assert_called_once_with(refund_id=refund_id, amount=200)
    
    uow_mock.sales.update.assert_called_once_with(sale)
    uow_mock.track.assert_called_once_with(sale)
    uow_mock.commit.assert_called_once()
    assert result.data == sale
