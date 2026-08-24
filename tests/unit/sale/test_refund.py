"""Unit tests for the Refund and RefundLine entities."""
from __future__ import annotations

import uuid

import pytest

from src.domains.sale.entities.enums import RefundStatus
from src.domains.sale.entities.refund import Refund
from src.domains.sale.entities.refund_line import RefundLine


@pytest.fixture
def sample_refund_line():
    return RefundLine.create(
        refund_id=uuid.uuid4(),
        sale_line_id=uuid.uuid4(),
        quantity=2,
    )


def test_refund_line_create():
    sale_line_id = uuid.uuid4()
    line = RefundLine.create(refund_id=uuid.uuid4(), sale_line_id=sale_line_id, quantity=3)

    assert line.sale_line_id == sale_line_id
    assert line.quantity == 3
    assert isinstance(line.id, uuid.UUID)


@pytest.mark.parametrize("quantity", [0, -1, -5])
def test_refund_line_create_rejects_non_positive_quantity(quantity):
    with pytest.raises(ValueError, match="Refund line quantity must be positive"):
        RefundLine.create(refund_id=uuid.uuid4(), sale_line_id=uuid.uuid4(), quantity=quantity)


def test_refund_create_success(sample_refund_line):
    sale_id = uuid.uuid4()
    processed_by = uuid.uuid4()

    refund = Refund.create(
        sale_id=sale_id,
        processed_by=processed_by,
        reason="Defective item",
        lines=[sample_refund_line],
    )

    assert refund.sale_id == sale_id
    assert refund.processed_by == processed_by
    assert refund.reason == "Defective item"
    assert refund.status == RefundStatus.PENDING
    assert refund.lines == [sample_refund_line]


def test_refund_create_sets_refund_id_on_lines(sample_refund_line):
    # The line's refund_id is populated after the refund is created, since the
    # refund id doesn't exist beforehand.
    original_refund_id = sample_refund_line.refund_id

    refund = Refund.create(
        sale_id=uuid.uuid4(),
        processed_by=uuid.uuid4(),
        reason="Wrong size",
        lines=[sample_refund_line],
    )

    assert sample_refund_line.refund_id == refund.id
    assert sample_refund_line.refund_id != original_refund_id


def test_refund_create_requires_at_least_one_line():
    with pytest.raises(ValueError, match="Refund must have at least one line"):
        Refund.create(
            sale_id=uuid.uuid4(),
            processed_by=uuid.uuid4(),
            reason="No lines",
            lines=[],
        )


def test_refund_mark_processed(sample_refund_line):
    refund = Refund.create(
        sale_id=uuid.uuid4(),
        processed_by=uuid.uuid4(),
        reason="Reason",
        lines=[sample_refund_line],
    )

    refund.mark_processed()

    assert refund.status == RefundStatus.PROCESSED


def test_refund_mark_processed_twice_raises(sample_refund_line):
    refund = Refund.create(
        sale_id=uuid.uuid4(),
        processed_by=uuid.uuid4(),
        reason="Reason",
        lines=[sample_refund_line],
    )
    refund.mark_processed()

    with pytest.raises(ValueError, match="Cannot process refund in processed state"):
        refund.mark_processed()


def test_refund_mark_failed(sample_refund_line):
    refund = Refund.create(
        sale_id=uuid.uuid4(),
        processed_by=uuid.uuid4(),
        reason="Reason",
        lines=[sample_refund_line],
    )

    refund.mark_failed()

    assert refund.status == RefundStatus.FAILED


def test_refund_mark_failed_when_not_pending_raises(sample_refund_line):
    refund = Refund.create(
        sale_id=uuid.uuid4(),
        processed_by=uuid.uuid4(),
        reason="Reason",
        lines=[sample_refund_line],
    )
    refund.mark_failed()

    with pytest.raises(ValueError, match="Cannot fail refund in failed state"):
        refund.mark_failed()


def test_refund_mark_processed_after_failed_raises(sample_refund_line):
    refund = Refund.create(
        sale_id=uuid.uuid4(),
        processed_by=uuid.uuid4(),
        reason="Reason",
        lines=[sample_refund_line],
    )
    refund.mark_failed()

    with pytest.raises(ValueError, match="Cannot process refund in failed state"):
        refund.mark_processed()