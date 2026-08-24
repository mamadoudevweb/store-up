import uuid
import pytest
from src.domains.sale.entities.sale import Sale
from src.domains.sale.entities.sale_line import SaleLine
from src.domains.sale.entities.enums import SaleStatus
from src.domains.sale.exceptions import InvalidSaleStateError
from src.domains.sale.events import SaleCreated


@pytest.fixture
def sample_sale_lines():
    return [
        SaleLine.create(
            sale_id=uuid.uuid4(),
            variant_id=uuid.uuid4(),
            quantity=2,
            unit_price=100,
        )
    ]


def test_sale_creation(sample_sale_lines):
    seller_id = uuid.uuid4()
    payment_id = uuid.uuid4()
    
    sale = Sale.checkout(
        seller_account_id=seller_id,
        payment_method_id=payment_id,
        lines=sample_sale_lines,
    )
    
    assert sale.status == SaleStatus.PENDING
    assert sale.total == 200
    
    # Verify domain event
    assert len(sale._events) == 1
    event = sale._events[0]
    assert isinstance(event, SaleCreated)
    assert event.total == 200


def test_sale_completion(sample_sale_lines):
    sale = Sale.checkout(
        seller_account_id=uuid.uuid4(),
        payment_method_id=uuid.uuid4(),
        lines=sample_sale_lines,
    )
    sale.id = uuid.uuid4()
    
    sale._events.clear()
    sale.mark_completed()
    
    assert sale.status == SaleStatus.COMPLETED
    assert len(sale._events) == 1
    
    from src.domains.sale.events import SaleCompleted
    event = sale._events[0]
    assert isinstance(event, SaleCompleted)


def test_sale_fail(sample_sale_lines):
    sale = Sale.checkout(
        seller_account_id=uuid.uuid4(),
        payment_method_id=uuid.uuid4(),
        lines=sample_sale_lines,
    )
    
    sale._events.clear()
    sale.mark_failed("Payment declined")
    
    assert sale.status == SaleStatus.FAILED
    assert sale.failed_at is not None


def test_invalid_state_transition(sample_sale_lines):
    sale = Sale.checkout(
        seller_account_id=uuid.uuid4(),
        payment_method_id=uuid.uuid4(),
        lines=sample_sale_lines,
    )
    
    sale.mark_completed()
    
    with pytest.raises(InvalidSaleStateError):
        sale.mark_failed("Late fail")


def test_sale_line_negative_discount():
    with pytest.raises(ValueError, match="Discount cannot be negative"):
        SaleLine.create(
            sale_id=uuid.uuid4(),
            variant_id=uuid.uuid4(),
            quantity=1,
            unit_price=100,
            discount=-10
        )


def test_sale_line_discount_exceeds_unit_price():
    with pytest.raises(ValueError, match="Discount cannot exceed unit price"):
        SaleLine.create(
            sale_id=uuid.uuid4(),
            variant_id=uuid.uuid4(),
            quantity=1,
            unit_price=100,
            discount=150
        )


def test_sale_checkout_negative_discount(sample_sale_lines):
    with pytest.raises(ValueError, match="Order-level discount cannot be negative"):
        Sale.checkout(
            seller_account_id=uuid.uuid4(),
            payment_method_id=uuid.uuid4(),
            lines=sample_sale_lines,
            discount=-50
        )
