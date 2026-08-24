from src.core.docs.openapi_registry import spec
from src.domains.catalog.routes.v1.schemas.product_schemas import (
    BrandResponse, CreateBrandRequest, UpdateBrandRequest,
    CategoryResponse, CreateCategoryRequest, UpdateCategoryRequest,
    ProductResponse, CreateProductRequest, UpdateProductRequest,
    ProductVariantResponse, CreateVariantRequest, UpdateVariantRequest,
    AttributeResponse, CreateAttributeRequest
)

def register() -> None:
    # --- BRANDS ---
    spec.path(
        path="/api/v1/brands",
        operations={
            "get": {
                "tags": ["Catalog / Brands"],
                "summary": "List brands",
                "responses": {"200": {"description": "Paginated list of brands"}},
            },
            "post": {
                "tags": ["Catalog / Brands"],
                "summary": "Create brand",
                "requestBody": {"content": {"application/json": {"schema": CreateBrandRequest.model_json_schema()}}},
                "responses": {"201": {"content": {"application/json": {"schema": BrandResponse.model_json_schema()}}}},
            }
        }
    )
    spec.path(
        path="/api/v1/brands/{brand_id}",
        operations={
            "get": {
                "tags": ["Catalog / Brands"],
                "summary": "Get brand",
                "parameters": [{"name": "brand_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {"200": {"content": {"application/json": {"schema": BrandResponse.model_json_schema()}}}},
            }
        }
    )
    
    # --- CATEGORIES ---
    spec.path(
        path="/api/v1/categories",
        operations={
            "get": {
                "tags": ["Catalog / Categories"],
                "summary": "List categories",
                "responses": {"200": {"description": "Paginated list of categories"}},
            },
            "post": {
                "tags": ["Catalog / Categories"],
                "summary": "Create category",
                "requestBody": {"content": {"application/json": {"schema": CreateCategoryRequest.model_json_schema()}}},
                "responses": {"201": {"content": {"application/json": {"schema": CategoryResponse.model_json_schema()}}}},
            }
        }
    )
    spec.path(
        path="/api/v1/categories/{category_id}",
        operations={
            "get": {
                "tags": ["Catalog / Categories"],
                "summary": "Get category",
                "parameters": [{"name": "category_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {"200": {"content": {"application/json": {"schema": CategoryResponse.model_json_schema()}}}},
            }
        }
    )
    
    # --- ATTRIBUTES ---
    spec.path(
        path="/api/v1/attributes",
        operations={
            "get": {
                "tags": ["Catalog / Attributes"],
                "summary": "List attributes",
                "responses": {"200": {"description": "Paginated list of attributes"}},
            },
            "post": {
                "tags": ["Catalog / Attributes"],
                "summary": "Create attribute",
                "requestBody": {"content": {"application/json": {"schema": CreateAttributeRequest.model_json_schema()}}},
                "responses": {"201": {"content": {"application/json": {"schema": AttributeResponse.model_json_schema()}}}},
            }
        }
    )
    
    # --- PRODUCTS ---
    spec.path(
        path="/api/v1/products",
        operations={
            "get": {
                "tags": ["Catalog / Products"],
                "summary": "List products",
                "responses": {"200": {"description": "Paginated list of products"}},
            },
            "post": {
                "tags": ["Catalog / Products"],
                "summary": "Create product",
                "requestBody": {"content": {"application/json": {"schema": CreateProductRequest.model_json_schema()}}},
                "responses": {"201": {"content": {"application/json": {"schema": ProductResponse.model_json_schema()}}}},
            }
        }
    )
    spec.path(
        path="/api/v1/products/{product_id}",
        operations={
            "get": {
                "tags": ["Catalog / Products"],
                "summary": "Get product",
                "parameters": [{"name": "product_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {"200": {"content": {"application/json": {"schema": ProductResponse.model_json_schema()}}}},
            }
        }
    )
    
    # --- PRODUCT VARIANTS ---
    spec.path(
        path="/api/v1/products/{product_id}/variants",
        operations={
            "get": {
                "tags": ["Catalog / Product Variants"],
                "summary": "List product variants",
                "parameters": [{"name": "product_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "responses": {"200": {"description": "List of product variants"}},
            },
            "post": {
                "tags": ["Catalog / Product Variants"],
                "summary": "Create product variant",
                "parameters": [{"name": "product_id", "in": "path", "required": True, "schema": {"type": "string", "format": "uuid"}}],
                "requestBody": {"content": {"application/json": {"schema": CreateVariantRequest.model_json_schema()}}},
                "responses": {"201": {"content": {"application/json": {"schema": ProductVariantResponse.model_json_schema()}}}},
            }
        }
    )
