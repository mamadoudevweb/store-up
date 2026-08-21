"""Catalog repository mappers — Entity ↔ ORM model."""
from __future__ import annotations

from src.core.repositories.utils import Mapper
from src.domains.catalog.entities import Brand, Category, Product, ProductImage
from src.domains.catalog.repositories.sql.orms import (
    BrandModel,
    CategoryModel,
    ProductImageModel,
    ProductModel,
)


class CategoryMapper(Mapper[Category, CategoryModel]):
    def to_entity(self, model: CategoryModel) -> Category:
        return Category(
            id=model.id,
            name=model.name,
            parent_id=model.parent_id,
        )

    def to_model(self, entity: Category, model: CategoryModel | None = None) -> CategoryModel:
        m = model or CategoryModel()
        m.id = entity.id
        m.name = entity.name
        m.parent_id = entity.parent_id
        return m


class BrandMapper(Mapper[Brand, BrandModel]):
    def to_entity(self, model: BrandModel) -> Brand:
        return Brand(
            id=model.id,
            name=model.name,
            description=model.description,
            logo_path=model.logo_path,
            is_active=model.is_active,
        )

    def to_model(self, entity: Brand, model: BrandModel | None = None) -> BrandModel:
        m = model or BrandModel()
        m.id = entity.id
        m.name = entity.name
        m.description = entity.description
        m.logo_path = entity.logo_path
        m.is_active = entity.is_active
        return m


class ProductMapper(Mapper[Product, ProductModel]):
    def to_entity(self, model: ProductModel) -> Product:
        return Product(
            id=model.id,
            sku=model.sku,
            name=model.name,
            cost_price=model.cost_price,
            sell_price=model.sell_price,
            description=model.description,
            category_id=model.category_id,
            brand_id=model.brand_id,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def to_model(self, entity: Product, model: ProductModel | None = None) -> ProductModel:
        m = model or ProductModel()
        m.id = entity.id
        m.sku = entity.sku
        m.name = entity.name
        m.description = entity.description
        m.cost_price = entity.cost_price
        m.sell_price = entity.sell_price
        m.category_id = entity.category_id
        m.brand_id = entity.brand_id
        m.is_active = entity.is_active
        m.created_at = entity.created_at
        m.updated_at = entity.updated_at
        return m


class ProductImageMapper(Mapper[ProductImage, ProductImageModel]):
    def to_entity(self, model: ProductImageModel) -> ProductImage:
        return ProductImage(
            id=model.id,
            product_id=model.product_id,
            file_path=model.file_path,
            is_primary=model.is_primary,
            sort_order=model.sort_order,
            created_at=model.created_at,
        )

    def to_model(
        self, entity: ProductImage, model: ProductImageModel | None = None
    ) -> ProductImageModel:
        m = model or ProductImageModel()
        m.id = entity.id
        m.product_id = entity.product_id
        m.file_path = entity.file_path
        m.is_primary = entity.is_primary
        m.sort_order = entity.sort_order
        m.created_at = entity.created_at
        return m
