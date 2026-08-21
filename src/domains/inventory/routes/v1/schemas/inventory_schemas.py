"""Inventory Pydantic schemas."""
from pydantic import BaseModel, ConfigDict, Field


class AdjustStockRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    quantity_change: int
    reason: str = Field(max_length=50)
    reference_id: str | None = Field(default=None, max_length=100)


class ReserveStockRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    quantity: int = Field(gt=0)
    reference_id: str | None = Field(default=None, max_length=100)


class SetLowStockThresholdRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    threshold: int = Field(ge=0)


class InventoryItemOutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    product_id: str
    quantity_on_hand: int
    quantity_reserved: int
    low_stock_threshold: int
    available_quantity: int


class StockMovementOutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    product_id: str
    quantity_change: int
    reason: str
    reference_id: str | None
    created_at: str
