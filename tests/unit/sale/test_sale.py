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


def test_sale_checkout_requires_at_least_one_line():
    with pytest.raises(ValueError, match="Sale must have at least one line"):
        Sale.checkout(
            seller_account_id=uuid.uuid4(),
            payment_method_id=uuid.uuid4(),
            lines=[],
        )


def test_sale_checkout_discount_exceeding_subtotal_raises(sample_sale_lines):
    # subtotal is 200 (2 * 100), a discount larger than that yields a negative total
    with pytest.raises(ValueError, match="Total cannot be negative"):
        Sale.checkout(
            seller_account_id=uuid.uuid4(),
            payment_method_id=uuid.uuid4(),
            lines=sample_sale_lines,
            discount=500,
        )


def test_sale_checkout_generates_number_when_not_provided(sample_sale_lines):
    sale = Sale.checkout(
        seller_account_id=uuid.uuid4(),
        payment_method_id=uuid.uuid4(),
        lines=sample_sale_lines,
    )

    assert sale.number is not None
    assert sale.number.startswith("SALE-")


def test_sale_checkout_uses_provided_number(sample_sale_lines):
    sale = Sale.checkout(
        seller_account_id=uuid.uuid4(),
        payment_method_id=uuid.uuid4(),
        lines=sample_sale_lines,
        number="CUSTOM-NUMBER-1",
    )

    assert sale.number == "CUSTOM-NUMBER-1"


def test_sale_checkout_assigns_sale_id_to_all_lines():
    lines = [
        SaleLine.create(sale_id=uuid.uuid4(), variant_id=uuid.uuid4(), quantity=1, unit_price=50),
        SaleLine.create(sale_id=uuid.uuid4(), variant_id=uuid.uuid4(), quantity=1, unit_price=25),
    ]

    sale = Sale.checkout(
        seller_account_id=uuid.uuid4(),
        payment_method_id=uuid.uuid4(),
        lines=lines,
    )

    assert all(line.sale_id == sale.id for line in sale.lines)


def test_sale_mark_completed_twice_raises(sample_sale_lines):
    sale = Sale.checkout(
        seller_account_id=uuid.uuid4(),
        payment_method_id=uuid.uuid4(),
        lines=sample_sale_lines,
    )
    sale.mark_completed()

    with pytest.raises(InvalidSaleStateError, match="Only pending sales can be completed"):
        sale.mark_completed()


def test_sale_mark_failed_sets_failed_at(sample_sale_lines):
    sale = Sale.checkout(
        seller_account_id=uuid.uuid4(),
        payment_method_id=uuid.uuid4(),
        lines=sample_sale_lines,
    )

    assert sale.failed_at is None
    sale.mark_failed("Card declined")

    assert sale.failed_at is not None


def test_sale_process_refund_from_completed(sample_sale_lines):
    sale = Sale.checkout(
        seller_account_id=uuid.uuid4(),
        payment_method_id=uuid.uuid4(),
        lines=sample_sale_lines,
    )
    sale.mark_completed()
    sale._events.clear()

    for line in sale.lines:
        line.refunded_quantity = line.quantity

    refund_id = uuid.uuid4()
    refunded_variant_id = sale.lines[0].variant_id
    sale.process_refund(
        refund_id=refund_id,
        amount=150,
        refund_lines=[
            {
                "sale_line_id": sale.lines[0].id,
                "variant_id": refunded_variant_id,
                "quantity": 2,
            }
        ],
    )

    assert sale.status == SaleStatus.RETURNED
    assert sale.returned_at is not None

    from src.domains.sale.events import SaleReturned, RefundCompleted
    assert len(sale._events) == 2
    assert isinstance(sale._events[0], RefundCompleted)
    assert sale._events[0].lines == [
        {"variant_id": refunded_variant_id, "quantity": 2}
    ]
    event = sale._events[1]
    assert isinstance(event, SaleReturned)
    assert event.refund_id == refund_id
    assert event.sale_id == sale.id
    assert event.amount == 150


def test_sale_process_refund_from_returned_is_allowed(sample_sale_lines):
    # A second partial refund on an already fully-refunded sale is allowed by
    # the entity - the guard only rejects pending/failed sales.
    sale = Sale.checkout(
        seller_account_id=uuid.uuid4(),
        payment_method_id=uuid.uuid4(),
        lines=sample_sale_lines,
    )
    sale.mark_completed()
    for line in sale.lines:
        line.refunded_quantity = line.quantity
    sale.process_refund(refund_id=uuid.uuid4(), amount=100, refund_lines=[])

    # Should not raise
    sale.process_refund(refund_id=uuid.uuid4(), amount=50, refund_lines=[])
    assert sale.status == SaleStatus.RETURNED


def test_sale_process_refund_from_pending_raises(sample_sale_lines):
    sale = Sale.checkout(
        seller_account_id=uuid.uuid4(),
        payment_method_id=uuid.uuid4(),
        lines=sample_sale_lines,
    )

    with pytest.raises(InvalidSaleStateError, match="Sale must be completed to process a refund"):
        sale.process_refund(refund_id=uuid.uuid4(), amount=50, refund_lines=[])


def test_sale_process_refund_from_failed_raises(sample_sale_lines):
    sale = Sale.checkout(
        seller_account_id=uuid.uuid4(),
        payment_method_id=uuid.uuid4(),
        lines=sample_sale_lines,
    )
    sale.mark_failed("Payment declined")

    with pytest.raises(InvalidSaleStateError, match="Sale must be completed to process a refund"):
        sale.process_refund(refund_id=uuid.uuid4(), amount=50, refund_lines=[])


@pytest.mark.parametrize("quantity", [0, -1])
def test_sale_line_rejects_non_positive_quantity(quantity):
    with pytest.raises(ValueError, match="Sale line quantity must be positive"):
        SaleLine.create(
            sale_id=uuid.uuid4(),
            variant_id=uuid.uuid4(),
            quantity=quantity,
            unit_price=100,
        )


def test_sale_line_rejects_negative_unit_price():
    with pytest.raises(ValueError, match="Unit price cannot be negative"):
        SaleLine.create(
            sale_id=uuid.uuid4(),
            variant_id=uuid.uuid4(),
            quantity=1,
            unit_price=-10,
        )


def test_sale_line_subtotal_computation():
    line = SaleLine.create(
        sale_id=uuid.uuid4(),
        variant_id=uuid.uuid4(),
        quantity=3,
        unit_price=50,
        discount=10,
    )

    assert line.subtotal == (50 - 10) * 3
    assert line.refunded_quantity == 0


def test_sale_line_zero_discount_is_allowed():
    line = SaleLine.create(
        sale_id=uuid.uuid4(),
        variant_id=uuid.uuid4(),
        quantity=1,
        unit_price=0,
        discount=0,
    )

    assert line.subtotal == 0
