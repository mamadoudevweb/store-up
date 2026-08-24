"""Exceptions for the Stock domain."""
from src.core.services.errors import ConflictError, NotFoundError


class StockItemNotFound(NotFoundError):
    code, message = "STOCK_ITEM_NOT_FOUND", "Stock item not found"


class StockMovementNotFound(NotFoundError):
    code, message = "STOCK_MOVEMENT_NOT_FOUND", "Stock movement not found"


class InsufficientStockError(ConflictError):
    code, message = "STOCK_INSUFFICIENT_STOCK", "Insufficient stock available"


class InsufficientReservedStockError(ConflictError):
    code, message = "STOCK_INSUFFICIENT_RESERVED", "Insufficient reserved stock"
