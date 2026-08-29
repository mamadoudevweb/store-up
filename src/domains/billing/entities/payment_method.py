"""PaymentMethod entity — pure dataclass, no ORM/Flask imports."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.core.entities.base_entity import BaseEntity


@dataclass(kw_only=True)
class PaymentMethod(BaseEntity[uuid.UUID]):
    """Small, fixed, pre-registered lookup — not a per-customer wallet.

    Fields match spec §4.1.  `processor_key` is the pluggability hook that
    maps to a registered PaymentProcessor implementation.
    """
    id: uuid.UUID
    name: str
    processor_key: str
    is_active: bool

    @classmethod
    def create(
        cls,
        name: str,
        processor_key: str,
        is_active: bool = False,
    ) -> "PaymentMethod":
        if not name.strip():
            raise ValueError("PaymentMethod name cannot be empty")
        if not processor_key.strip():
            raise ValueError("PaymentMethod processor_key cannot be empty")
        return cls(
            id=uuid.uuid4(),
            name=name,
            processor_key=processor_key,
            is_active=is_active,
        )
