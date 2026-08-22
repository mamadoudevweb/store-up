"""Category entity."""
from __future__ import annotations
from uuid import UUID

import uuid
from dataclasses import dataclass

from src.core.entities.base_entity import BaseEntity


@dataclass(kw_only=True)
class Category(BaseEntity[UUID]):
    name: str
    parent_id: uuid.UUID | None = None
