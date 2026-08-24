"""Unit tests for sale domain enums."""
from __future__ import annotations

from src.domains.sale.entities.enums import RefundStatus, SaleStatus


def test_sale_status_values():
    assert SaleStatus.PENDING.value == "pending"
    assert SaleStatus.COMPLETED.value == "completed"
    assert SaleStatus.FAILED.value == "failed"
    assert SaleStatus.RETURNED.value == "returned"


def test_sale_status_is_str_enum():
    # SaleStatus subclasses str so it can be compared/serialized directly.
    assert SaleStatus.PENDING == "pending"
    assert isinstance(SaleStatus.PENDING, str)


def test_refund_status_values():
    assert RefundStatus.PENDING.value == "pending"
    assert RefundStatus.PROCESSED.value == "processed"
    assert RefundStatus.FAILED.value == "failed"


def test_refund_status_is_str_enum():
    assert RefundStatus.PROCESSED == "processed"
    assert isinstance(RefundStatus.PROCESSED, str)


def test_sale_status_members_are_unique():
    values = [member.value for member in SaleStatus]
    assert len(values) == len(set(values))


def test_refund_status_members_are_unique():
    values = [member.value for member in RefundStatus]
    assert len(values) == len(set(values))