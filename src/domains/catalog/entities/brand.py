"""Brand entity."""
from __future__ import annotations
from uuid import UUID

from dataclasses import dataclass

from src.core.entities.base_entity import BaseEntity


@dataclass(kw_only=True)
class Brand(BaseEntity[UUID]):
    name: str
    description: str | None = None
    logo_path: str | None = None
    is_active: bool = True
