"""Events for the Catalog domain."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.core.entities.events import DomainEvent


@dataclass(frozen=True)
class ProductCreated(DomainEvent):
    """Emitted when a new product is created."""
    product_id: uuid.UUID
