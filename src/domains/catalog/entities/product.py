"""Product entity."""
from __future__ import annotations
from uuid import UUID

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.core.entities.base_entity import BaseEntity


@dataclass(kw_only=True)
class Product(BaseEntity[UUID]):
    sku: str
    name: str
    cost_price: int  # in cents
    sell_price: int  # in cents
    description: str | None = None
    category_id: uuid.UUID | None = None
    brand_id: uuid.UUID | None = None
    is_active: bool = True
