"""Sale mappers."""
from __future__ import annotations

from src.core.repositories.utils import Mapper
from src.domains.sale.entities.sale import Sale
from src.domains.sale.entities.sale_line import SaleLine
from src.domains.sale.entities.refund import Refund
from src.domains.sale.entities.refund_line import RefundLine
from src.domains.sale.entities.enums import SaleStatus, RefundStatus
from src.domains.sale.repositories.sql.orms import SaleModel, SaleLineModel, RefundModel, RefundLineModel


class SaleLineMapper(Mapper[SaleLine, SaleLineModel]):
    def to_entity(self, model: SaleLineModel) -> SaleLine:
        """
        Convert a sale-line ORM model into a sale-line entity.
        
        Parameters:
        	model (SaleLineModel): The ORM model containing the sale-line data.
        
        Returns:
        	SaleLine: The corresponding sale-line entity.
        """
        return SaleLine(
            id=model.id,
            sale_id=model.sale_id,
            variant_id=model.variant_id,
            quantity=model.quantity,
            unit_price=model.unit_price,
            discount=model.discount,
            subtotal=model.subtotal,
            refunded_quantity=model.refunded_quantity,
        )

    def to_model(self, entity: SaleLine, model: SaleLineModel | None = None) -> SaleLineModel:
        """
        Create or update a sale-line ORM model from a sale-line entity.
        
        Parameters:
        	entity (SaleLine): The sale-line entity to map.
        	model (SaleLineModel | None): An existing ORM model to update.
        
        Returns:
        	SaleLineModel: The mapped sale-line ORM model.
        """
        m = model or SaleLineModel()
        m.id = entity.id
        m.sale_id = entity.sale_id
        m.variant_id = entity.variant_id
        m.quantity = entity.quantity
        m.unit_price = entity.unit_price
        m.discount = entity.discount
        m.subtotal = entity.subtotal
        m.refunded_quantity = entity.refunded_quantity
        return m


class SaleMapper(Mapper[Sale, SaleModel]):
    def __init__(self) -> None:
        self.line_mapper = SaleLineMapper()

    def to_entity(self, model: SaleModel) -> Sale:
        """
        Convert a sale ORM model and its line models into a sale domain entity.
        
        Parameters:
            model (SaleModel): The ORM model containing the sale data and associated lines.
        
        Returns:
            Sale: The reconstructed sale entity.
        """
        return Sale(
            id=model.id,
            number=model.number,
            customer_name=model.customer_name,
            seller_account_id=model.seller_account_id,
            status=SaleStatus(model.status),
            payment_method_id=model.payment_method_id,
            discount=model.discount,
            subtotal=model.subtotal,
            total=model.total,
            created_at=model.created_at,
            returned_at=model.returned_at,
            failed_at=model.failed_at,
            lines=[self.line_mapper.to_entity(line) for line in model.lines],
        )

    def to_model(self, entity: Sale, model: SaleModel | None = None) -> SaleModel:
        """Convert a sale entity to a sale ORM model.
        
        Parameters:
            entity (Sale): Sale data to persist.
            model (SaleModel | None): Existing model to update, or `None` to create one.
        
        Returns:
            SaleModel: The populated sale ORM model.
        """
        m = model or SaleModel()
        m.id = entity.id
        m.number = entity.number
        m.customer_name = entity.customer_name
        m.seller_account_id = entity.seller_account_id
        m.status = entity.status.value
        m.payment_method_id = entity.payment_method_id
        m.discount = entity.discount
        m.subtotal = entity.subtotal
        m.total = entity.total
        m.created_at = entity.created_at
        m.returned_at = entity.returned_at
        m.failed_at = entity.failed_at
        
        # We don't typically update lines via the SaleMapper directly to avoid 
        # complex list diffing, unless we rebuild the entire relationship. 
        # For our use case, lines are immutable after checkout.
        if not model and hasattr(entity, 'lines'):
            m.lines = [self.line_mapper.to_model(line) for line in entity.lines]
            
        return m


class RefundLineMapper(Mapper[RefundLine, RefundLineModel]):
    def to_entity(self, model: RefundLineModel) -> RefundLine:
        """
        Create a refund line entity from its ORM model.
        
        Parameters:
        	model (RefundLineModel): The ORM model containing the refund line data.
        
        Returns:
        	RefundLine: The corresponding refund line entity.
        """
        return RefundLine(
            id=model.id,
            refund_id=model.refund_id,
            sale_line_id=model.sale_line_id,
            quantity=model.quantity,
        )

    def to_model(self, entity: RefundLine, model: RefundLineModel | None = None) -> RefundLineModel:
        """
        Map a refund line entity to a SQL ORM model.
        
        Parameters:
            entity (RefundLine): The refund line to map.
            model (RefundLineModel | None): An existing model to update, or `None` to create one.
        
        Returns:
            RefundLineModel: The populated refund line model.
        """
        m = model or RefundLineModel()
        m.id = entity.id
        m.refund_id = entity.refund_id
        m.sale_line_id = entity.sale_line_id
        m.quantity = entity.quantity
        return m


class RefundMapper(Mapper[Refund, RefundModel]):
    def __init__(self) -> None:
        self.line_mapper = RefundLineMapper()

    def to_entity(self, model: RefundModel) -> Refund:
        """
        Convert a refund ORM model into a domain entity.
        
        Parameters:
        	model (RefundModel): The ORM model containing the refund data and lines.
        
        Returns:
        	Refund: A refund entity with its status and nested lines reconstructed.
        """
        return Refund(
            id=model.id,
            sale_id=model.sale_id,
            processed_by=model.processed_by,
            reason=model.reason,
            status=RefundStatus(model.status),
            created_at=model.created_at,
            lines=[self.line_mapper.to_entity(line) for line in model.lines],
        )

    def to_model(self, entity: Refund, model: RefundModel | None = None) -> RefundModel:
        """
        Create or update a refund ORM model from a refund entity.
        
        Parameters:
        	entity (Refund): The refund entity to map.
        	model (RefundModel | None): An existing model to update, or None to create one.
        
        Returns:
        	RefundModel: The populated refund ORM model.
        """
        m = model or RefundModel()
        m.id = entity.id
        m.sale_id = entity.sale_id
        m.processed_by = entity.processed_by
        m.reason = entity.reason
        m.status = entity.status.value
        m.created_at = entity.created_at
        
        if not model and hasattr(entity, 'lines'):
            m.lines = [self.line_mapper.to_model(line) for line in entity.lines]
            
        return m
