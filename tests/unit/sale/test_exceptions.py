"""Unit tests for sale domain exceptions."""
from __future__ import annotations

import pytest

from src.core.services.errors import ConflictError, NotFoundError
from src.domains.sale.exceptions import (
    InsufficientStockError,
    InvalidSaleStateError,
    RefundNotFoundError,
    RefundQuantityExceededError,
    SaleLineNotFoundError,
    SaleNotFoundError,
)


@pytest.mark.parametrize(
    "exc_cls, base_cls, code, status_code",
    [
        (InsufficientStockError, ConflictError, "INSUFFICIENT_STOCK", 409),
        (SaleNotFoundError, NotFoundError, "SALE_NOT_FOUND", 404),
        (InvalidSaleStateError, ConflictError, "INVALID_SALE_STATE", 409),
        (RefundNotFoundError, NotFoundError, "REFUND_NOT_FOUND", 404),
        (SaleLineNotFoundError, NotFoundError, "SALE_LINE_NOT_FOUND", 404),
        (RefundQuantityExceededError, ConflictError, "REFUND_QUANTITY_EXCEEDED", 409),
    ],
)
def test_sale_exception_metadata(exc_cls, base_cls, code, status_code):
    assert issubclass(exc_cls, base_cls)
    assert exc_cls.code == code
    assert exc_cls.status_code == status_code
    assert exc_cls.message


def test_sale_exception_default_message():
    error = SaleNotFoundError()
    assert error.message == SaleNotFoundError.message
    assert error.details == {}


def test_sale_exception_custom_message_and_details():
    error = InsufficientStockError("Custom message", variant_id="abc-123")
    assert str(error) == "Custom message"
    assert error.message == "Custom message"
    assert error.details == {"variant_id": "abc-123"}


def test_sale_exceptions_are_registered_in_app_error_registry():
    from src.core.services.errors import ERROR_REGISTRY

    assert ERROR_REGISTRY["INSUFFICIENT_STOCK"] is InsufficientStockError
    assert ERROR_REGISTRY["SALE_NOT_FOUND"] is SaleNotFoundError
    assert ERROR_REGISTRY["INVALID_SALE_STATE"] is InvalidSaleStateError
    assert ERROR_REGISTRY["REFUND_NOT_FOUND"] is RefundNotFoundError
    assert ERROR_REGISTRY["SALE_LINE_NOT_FOUND"] is SaleLineNotFoundError
    assert ERROR_REGISTRY["REFUND_QUANTITY_EXCEEDED"] is RefundQuantityExceededError