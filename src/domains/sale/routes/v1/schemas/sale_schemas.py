import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class SaleLineInput(BaseModel):
    variant_id: uuid.UUID
    quantity: int = Field(gt=0)
    unit_price: int = Field(ge=0)
    discount: int = Field(ge=0, default=0)


class CheckoutRequest(BaseModel):
    seller_account_id: uuid.UUID
    payment_method_id: uuid.UUID
    lines: list[SaleLineInput] = Field(min_length=1)
    customer_name: str | None = None
    discount: int = Field(ge=0, default=0)
    sale_number: str | None = None


class SaleLineResponse(BaseModel):
    id: uuid.UUID
    variant_id: uuid.UUID
    quantity: int
    unit_price: int
    discount: int
    subtotal: int
    refunded_quantity: int
    
    model_config = ConfigDict(from_attributes=True)


class SaleResponse(BaseModel):
    id: uuid.UUID
    number: str | None
    customer_name: str | None
    seller_account_id: uuid.UUID
    status: str
    payment_method_id: uuid.UUID
    discount: int
    subtotal: int
    total: int
    created_at: datetime
    returned_at: datetime | None
    failed_at: datetime | None
    lines: list[SaleLineResponse]
    
    model_config = ConfigDict(from_attributes=True)


class RefundLineInput(BaseModel):
    sale_line_id: uuid.UUID
    quantity: int = Field(gt=0)


class RefundRequest(BaseModel):
    sale_id: uuid.UUID
    processed_by: uuid.UUID
    reason: str
    lines: list[RefundLineInput] = Field(min_length=1)


class RefundLineResponse(BaseModel):
    id: uuid.UUID
    sale_line_id: uuid.UUID
    quantity: int
    
    model_config = ConfigDict(from_attributes=True)


class RefundResponse(BaseModel):
    id: uuid.UUID
    sale_id: uuid.UUID
    processed_by: uuid.UUID
    reason: str
    status: str
    created_at: datetime
    lines: list[RefundLineResponse]
    
    model_config = ConfigDict(from_attributes=True)
