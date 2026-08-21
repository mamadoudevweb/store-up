"""Category entity."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.core.entities.base_entity import BaseEntity


@dataclass(kw_only=True)
class Category(BaseEntity):
    name: str
    parent_id: uuid.UUID | None = None
