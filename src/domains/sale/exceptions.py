from src.core.services.errors import ConflictError, NotFoundError

class InsufficientStockError(ConflictError):
    code, message = "INSUFFICIENT_STOCK", "Not enough stock to complete the sale."

class SaleNotFoundError(NotFoundError):
    code, message = "SALE_NOT_FOUND", "Sale not found."

class InvalidSaleStateError(ConflictError):
    code, message = "INVALID_SALE_STATE", "Sale is in an invalid state for this operation."

class RefundNotFoundError(NotFoundError):
    code, message = "REFUND_NOT_FOUND", "Refund not found."

class SaleLineNotFoundError(NotFoundError):
    code, message = "SALE_LINE_NOT_FOUND", "Sale line not found."

class RefundQuantityExceededError(ConflictError):
    code, message = "REFUND_QUANTITY_EXCEEDED", "Cannot refund more than the sold quantity."
