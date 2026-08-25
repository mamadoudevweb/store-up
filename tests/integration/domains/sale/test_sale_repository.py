import uuid
import pytest
from src.domains.sale.entities.sale import Sale
from src.domains.sale.entities.sale_line import SaleLine
from src.domains.sale.entities.enums import SaleStatus
from src.domains.sale.repositories.filters import SaleFilters

def test_add_sale(uow_factory):
    sale = Sale.checkout(
        seller_account_id=uuid.uuid4(),
        payment_method_id=uuid.uuid4(),
        customer_name="John Doe",
        lines=[
            SaleLine(
                id=uuid.uuid4(),
                sale_id=uuid.UUID(int=0), # placeholder
                variant_id=uuid.uuid4(),
                quantity=2,
                unit_price=100,
                discount=0,
                subtotal=200,
                refunded_quantity=0,
            )
        ]
    )
    sale_id = sale.id
    
    with uow_factory() as uow:
        uow.sales.add(sale)
        uow.commit()
        
    with uow_factory() as uow:
        retrieved_sale = uow.sales.get(sale_id)
        assert retrieved_sale is not None
        assert retrieved_sale.id == sale_id
        assert retrieved_sale.customer_name == "John Doe"
        assert len(retrieved_sale.lines) == 1
        assert retrieved_sale.lines[0].quantity == 2
        assert retrieved_sale.lines[0].unit_price == 100

def test_update_sale(uow_factory):
    sale = Sale.checkout(
        seller_account_id=uuid.uuid4(),
        payment_method_id=uuid.uuid4(),
        lines=[
            SaleLine(
                id=uuid.uuid4(),
                sale_id=uuid.UUID(int=0),
                variant_id=uuid.uuid4(),
                quantity=1,
                unit_price=100,
                discount=0,
                subtotal=100,
                refunded_quantity=0,
            )
        ]
    )
    sale_id = sale.id
    
    with uow_factory() as uow:
        uow.sales.add(sale)
        uow.commit()
        
    with uow_factory() as uow:
        retrieved_sale = uow.sales.get(sale_id)
        retrieved_sale.mark_completed()
        uow.sales.update(retrieved_sale)
        uow.commit()
        
    with uow_factory() as uow:
        updated_sale = uow.sales.get(sale_id)
        assert updated_sale.status == SaleStatus.COMPLETED

def test_find_sales(uow_factory):
    seller_id = uuid.uuid4()
    
    def create_sale():
        """
        Create a sale for the configured seller with one line item.
        """
        return Sale.checkout(
            seller_account_id=seller_id,
            payment_method_id=uuid.uuid4(),
            lines=[SaleLine(id=uuid.uuid4(), sale_id=uuid.UUID(int=0), variant_id=uuid.uuid4(), quantity=1, unit_price=10, discount=0, subtotal=10, refunded_quantity=0)]
        )
        
    sale1 = create_sale()
    sale2 = create_sale()
    sale2.mark_completed()
    
    with uow_factory() as uow:
        uow.sales.add(sale1)
        uow.sales.add(sale2)
        uow.commit()
        
    with uow_factory() as uow:
        results = uow.sales.list(SaleFilters(seller_account_id=seller_id))
        
    assert results.total == 2
    assert len(results.items) == 2
    assert any(s.id == sale1.id for s in results.items)
    assert any(s.id == sale2.id for s in results.items)
        
    with uow_factory() as uow:
        results = uow.sales.list(SaleFilters(seller_account_id=seller_id, status=SaleStatus.COMPLETED.value))
        assert results.total >= 1
        assert any(s.id == sale2.id for s in results.items)
