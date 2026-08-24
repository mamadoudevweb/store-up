from enum import Enum

class StockMovementReason(str, Enum):
    RESTOCK = "restock"
    ORDER_SHIPPED = "order_shipped"
    MANUAL_ADJUSTMENT = "manual_adjustment"
    RETURN = "return"
    DAMAGE = "damage"

class ReferenceType(str, Enum):
    SALE = "sale"
    PURCHASE_ORDER = "purchase_order"
    MANUAL_ADJUSTMENT = "manual_adjustment"
    RETURN = "return"
