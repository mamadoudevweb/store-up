"""Unit tests for sale domain events."""
from __future__ import annotations

import dataclasses
import uuid

import pytest

from src.domains.sale.events import (
    RefundRequested,
    SaleCompleted,
    SaleCreated,
    SaleFailed,
    SaleReturned,
)


def test_sale_created_event_defaults():
    sale_id = uuid.uuid4()
    seller_account_id = uuid.uuid4()
    payment_method_id = uuid.uuid4()

    event = SaleCreated(
        sale_id=sale_id,
        seller_account_id=seller_account_id,
        total=100,
        payment_method_id=payment_method_id,
    )

    assert event.sale_id == sale_id
    assert event.seller_account_id == seller_account_id
    assert event.total == 100
    assert event.payment_method_id == payment_method_id
    assert event.event_name == "sale_created"
    assert event.occurred_at is not None


def test_sale_failed_event_defaults():
    sale_id = uuid.uuid4()
    event = SaleFailed(sale_id=sale_id)

    assert event.sale_id == sale_id
    assert event.event_name == "sale_failed"


def test_sale_completed_event_defaults():
    sale_id = uuid.uuid4()
    event = SaleCompleted(sale_id=sale_id)

    assert event.sale_id == sale_id
    assert event.event_name == "sale_completed"


def test_sale_returned_event_defaults():
    refund_id = uuid.uuid4()
    sale_id = uuid.uuid4()
    event = SaleReturned(refund_id=refund_id, sale_id=sale_id, amount=250)

    assert event.refund_id == refund_id
    assert event.sale_id == sale_id
    assert event.amount == 250
    assert event.event_name == "sale_returned"


def test_refund_requested_event_defaults():
    refund_id = uuid.uuid4()
    sale_id = uuid.uuid4()
    sale_line_id = uuid.uuid4()
    lines_data = [{"sale_line_id": sale_line_id, "quantity": 2}]

    event = RefundRequested(
        refund_id=refund_id,
        sale_id=sale_id,
        amount=90,
        lines_data=lines_data,
    )

    assert event.refund_id == refund_id
    assert event.sale_id == sale_id
    assert event.amount == 90
    assert event.lines_data == lines_data
    assert event.event_name == "refund_requested"


@pytest.mark.parametrize(
    "event",
    [
        SaleCreated(sale_id=uuid.uuid4(), seller_account_id=uuid.uuid4(), total=1, payment_method_id=uuid.uuid4()),
        SaleFailed(sale_id=uuid.uuid4()),
        SaleCompleted(sale_id=uuid.uuid4()),
        SaleReturned(refund_id=uuid.uuid4(), sale_id=uuid.uuid4(), amount=1),
        RefundRequested(refund_id=uuid.uuid4(), sale_id=uuid.uuid4(), amount=1, lines_data=[]),
    ],
)
def test_sale_events_are_frozen(event):
    assert dataclasses.is_dataclass(event)
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.event_name = "mutated"  # type: ignore[misc]