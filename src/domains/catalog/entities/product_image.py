"""ProductImage entity."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.core.entities.base_entity import BaseEntity


@dataclass(kw_only=True)
class ProductImage(BaseEntity):
    product_id: uuid.UUID
    file_path: str
    is_primary: bool = False
    sort_order: int = 0
