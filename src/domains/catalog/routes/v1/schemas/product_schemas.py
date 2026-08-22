"""Products domain schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ── Category ──────────────────────────────────────────────────────────────────

class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    parent_id: UUID | None


class CreateCategoryRequest(BaseModel):
    name: str
    parent_id: UUID | None = None


class UpdateCategoryRequest(BaseModel):
    name: str
    parent_id: UUID | None = None


# ── Brand ─────────────────────────────────────────────────────────────────────

class BrandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    description: str | None
    logo_path: str | None
    is_active: bool


class CreateBrandRequest(BaseModel):
    name: str
    description: str | None = None


class UpdateBrandRequest(BaseModel):
    name: str
    description: str | None = None


# ── Product ───────────────────────────────────────────────────────────────────

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    sku: str
    name: str
    cost_price: int
    sell_price: int
    description: str | None
    category_id: UUID | None
    brand_id: UUID | None
    is_active: bool


class CreateProductRequest(BaseModel):
    sku: str
    name: str
    cost_price: int
    sell_price: int
    description: str | None = None
    category_id: UUID | None = None
    brand_id: UUID | None = None


class UpdateProductRequest(BaseModel):
    sku: str
    name: str
    cost_price: int
    sell_price: int
    description: str | None = None
    category_id: UUID | None = None
    brand_id: UUID | None = None
    is_active: bool = True


# ── ProductImage ──────────────────────────────────────────────────────────────

class ProductImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    product_id: UUID
    file_path: str
    is_primary: bool
    sort_order: int
