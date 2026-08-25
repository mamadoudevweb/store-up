"""Unit tests for sale domain event handlers."""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from src.core.events.dispatcher import EventDispatcher
from src.core.services.system_account import SystemAccount
from src.domains.sale import event_handlers
from src.domains.sale.events import RefundRequested, SaleReturned


@pytest.fixture
def domain_service_mock():
    return MagicMock()


@pytest.fixture
def dispatcher():
    return EventDispatcher()


def test_register_subscribes_to_refund_requested_and_sale_returned(dispatcher, domain_service_mock):
    event_handlers.register(dispatcher, domain_service_mock)

    assert len(dispatcher._handlers[RefundRequested]) == 1
    assert len(dispatcher._handlers[SaleReturned]) == 1


def test_on_refund_requested_calls_sale_service_process_refund(dispatcher, domain_service_mock):
    event_handlers.register(dispatcher, domain_service_mock)

    refund_id = uuid.uuid4()
    sale_id = uuid.uuid4()
    lines_data = [{"sale_line_id": uuid.uuid4(), "quantity": 1}]
    event = RefundRequested(refund_id=refund_id, sale_id=sale_id, amount=100, lines_data=lines_data)

    dispatcher.dispatch(event)

    domain_service_mock.sale.sale.process_refund.assert_called_once()
    _, kwargs = domain_service_mock.sale.sale.process_refund.call_args
    args = domain_service_mock.sale.sale.process_refund.call_args[0]

    assert isinstance(args[0], SystemAccount)
    assert kwargs["sale_id"] == sale_id
    assert kwargs["refund_id"] == refund_id
    assert kwargs["lines_data"] == lines_data
    assert kwargs["amount"] == 100


def test_on_sale_returned_calls_refund_service_complete_refund(dispatcher, domain_service_mock):
    event_handlers.register(dispatcher, domain_service_mock)

    refund_id = uuid.uuid4()
    event = SaleReturned(refund_id=refund_id, sale_id=uuid.uuid4(), amount=50)

    dispatcher.dispatch(event)

    domain_service_mock.sale.refund.complete_refund.assert_called_once()
    args = domain_service_mock.sale.refund.complete_refund.call_args[0]
    assert isinstance(args[0], SystemAccount)
    assert args[1] == refund_id


def test_register_does_not_trigger_handlers_for_unrelated_events(dispatcher, domain_service_mock):
    event_handlers.register(dispatcher, domain_service_mock)

    # Dispatching an event with no subscribers should not raise and should not
    # invoke unrelated handlers.
    from src.domains.sale.events import SaleCompleted

    dispatcher.dispatch(SaleCompleted(sale_id=uuid.uuid4()))

    domain_service_mock.sale.sale.process_refund.assert_not_called()
    domain_service_mock.sale.refund.complete_refund.assert_not_called()