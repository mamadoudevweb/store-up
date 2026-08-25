from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.core.entities.base_entity import BaseEntity


@dataclass(kw_only=True)
class SaleLine(BaseEntity[uuid.UUID]):
    id: uuid.UUID
    sale_id: uuid.UUID
    variant_id: uuid.UUID
    quantity: int
    unit_price: int
    discount: int
    subtotal: int
    refunded_quantity: int

    @classmethod
    def create(
        cls,
        sale_id: uuid.UUID,
        variant_id: uuid.UUID,
        quantity: int,
        unit_price: int,
        discount: int = 0,
    ) -> SaleLine:
        """
        Create a sale line with validated pricing and quantity details.
        
        Parameters:
            quantity (int): The number of units in the sale line.
            unit_price (int): The price per unit.
            discount (int): The discount applied to each unit.
        
        Returns:
            SaleLine: A new sale line with its discounted subtotal and no refunded units.
        
        Raises:
            ValueError: If quantity is not positive, unit price or discount is negative, or discount exceeds unit price.
        """
        if quantity <= 0:
            raise ValueError("Sale line quantity must be positive")
        if unit_price < 0:
            raise ValueError("Unit price cannot be negative")
        if discount < 0:
            raise ValueError("Discount cannot be negative")
        if discount > unit_price:
            raise ValueError("Discount cannot exceed unit price")
        
        return cls(
            id=uuid.uuid4(),
            sale_id=sale_id,
            variant_id=variant_id,
            quantity=quantity,
            unit_price=unit_price,
            discount=discount,
            subtotal=(unit_price - discount) * quantity,
            refunded_quantity=0,
        )
