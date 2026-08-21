"""Exceptions for the Inventory domain."""
from src.core.services.errors import ConflictError, NotFoundError


class InventoryItemNotFound(NotFoundError):
    code, message = "INVENTORY_ITEM_NOT_FOUND", "Inventory item not found"


class StockMovementNotFound(NotFoundError):
    code, message = "STOCK_MOVEMENT_NOT_FOUND", "Stock movement not found"


class InsufficientStockError(ConflictError):
    code, message = "INVENTORY_INSUFFICIENT_STOCK", "Insufficient stock available"


class InsufficientReservedStockError(ConflictError):
    code, message = "INVENTORY_INSUFFICIENT_RESERVED", "Insufficient reserved stock"
