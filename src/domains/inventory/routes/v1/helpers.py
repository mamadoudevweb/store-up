"""Inventory route helpers."""
from typing import TYPE_CHECKING
from flask import current_app

if TYPE_CHECKING:
    from src.app.domain_service import DomainService


def _get_inventory() -> Any:
    # Use Any return type here to avoid importing DomainService at runtime if not needed
    return current_app.extensions["domain_service"].inventory
