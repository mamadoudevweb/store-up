"""Catalog domain — Pydantic request/response schemas."""
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
    name: str
    description: str | None
    brand_id: UUID | None
    status: str


class CreateProductRequest(BaseModel):
    """Creates a Product + its first Variant atomically."""
    name: str
    description: str | None = None
    brand_id: UUID | None = None
    # First variant fields
    sku: str
    cost_price: int
    sell_price: int


class UpdateProductRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    brand_id: UUID | None = None


class ChangeStatusRequest(BaseModel):
    status: str  # "draft" | "active" | "archived"


# ── ProductVariant ─────────────────────────────────────────────────────────────

class ProductVariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    product_id: UUID
    sku: str
    cost_price: int
    sell_price: int
    status: str


class CreateVariantRequest(BaseModel):
    product_id: UUID
    sku: str
    cost_price: int
    sell_price: int


class UpdateVariantRequest(BaseModel):
    sku: str | None = None
    cost_price: int | None = None
    sell_price: int | None = None


# ── ProductCategory ────────────────────────────────────────────────────────────

class ProductCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_id: UUID
    category_id: UUID


class AssignCategoryRequest(BaseModel):
    category_id: UUID


# ── ProductImage ──────────────────────────────────────────────────────────────

class ProductImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    variant_id: UUID
    file_path: str
    order: int


# ── Attribute ─────────────────────────────────────────────────────────────────

class AttributeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str


class AttributeValueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    attribute_id: UUID
    value: str


class CreateAttributeRequest(BaseModel):
    name: str


class CreateAttributeValueRequest(BaseModel):
    value: str
