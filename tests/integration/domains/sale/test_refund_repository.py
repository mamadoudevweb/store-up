import uuid
import pytest
from src.domains.sale.entities.refund import Refund
from src.domains.sale.entities.refund_line import RefundLine
from src.domains.sale.entities.enums import RefundStatus
from src.domains.sale.repositories.filters import RefundFilters

def test_add_refund(uow_factory):
    sale_id = uuid.uuid4()
    refund = Refund.create(
        sale_id=sale_id,
        processed_by=uuid.uuid4(),
        reason="Defective",
        lines=[
            RefundLine(
                id=uuid.uuid4(),
                refund_id=uuid.UUID(int=0),
                sale_line_id=uuid.uuid4(),
                quantity=1
            )
        ]
    )
    refund_id = refund.id
    
    with uow_factory() as uow:
        uow.refunds.add(refund)
        uow.commit()
        
    with uow_factory() as uow:
        retrieved_refund = uow.refunds.get(refund_id)
        assert retrieved_refund is not None
        assert retrieved_refund.id == refund_id
        assert retrieved_refund.reason == "Defective"
        assert len(retrieved_refund.lines) == 1
        assert retrieved_refund.lines[0].quantity == 1

def test_update_refund(uow_factory):
    refund = Refund.create(
        sale_id=uuid.uuid4(),
        processed_by=uuid.uuid4(),
        reason="Not needed",
        lines=[
            RefundLine(
                id=uuid.uuid4(),
                refund_id=uuid.UUID(int=0),
                sale_line_id=uuid.uuid4(),
                quantity=1
            )
        ]
    )
    refund_id = refund.id
    
    with uow_factory() as uow:
        uow.refunds.add(refund)
        uow.commit()
        
    with uow_factory() as uow:
        retrieved = uow.refunds.get(refund_id)
        retrieved.mark_processed()
        uow.refunds.update(retrieved)
        uow.commit()
        
    with uow_factory() as uow:
        updated = uow.refunds.get(refund_id)
        assert updated.status == RefundStatus.PROCESSED

def test_find_refunds(uow_factory):
    sale_id = uuid.uuid4()
    
    def create_refund():
        return Refund.create(
            sale_id=sale_id,
            processed_by=uuid.uuid4(),
            reason="Reason",
            lines=[RefundLine(id=uuid.uuid4(), refund_id=uuid.UUID(int=0), sale_line_id=uuid.uuid4(), quantity=1)]
        )
        
    refund1 = create_refund()
    refund2 = create_refund()
    refund2.mark_processed()
    
    with uow_factory() as uow:
        uow.refunds.add(refund1)
        uow.refunds.add(refund2)
        uow.commit()
        
    with uow_factory() as uow:
        results = uow.refunds.list(RefundFilters(sale_id=sale_id))
        
    assert results.total == 2
    assert len(results.items) == 2
    assert any(r.id == refund1.id for r in results.items)
    assert any(r.id == refund2.id for r in results.items)
