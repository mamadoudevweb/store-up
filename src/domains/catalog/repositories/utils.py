"""Catalog repository mappers — Entity ↔ ORM model."""
from __future__ import annotations

from src.core.repositories.utils import Mapper
from src.domains.catalog.entities import (
    Attribute,
    AttributeValue,
    Brand,
    Category,
    Product,
    ProductCategory,
    ProductImage,
    ProductStatus,
    ProductVariant,
    ProductVariantAttribute,
    VariantStatus,
)
from src.domains.catalog.repositories.sql.orms import (
    AttributeModel,
    AttributeValueModel,
    BrandModel,
    CategoryModel,
    ProductCategoryModel,
    ProductImageModel,
    ProductModel,
    ProductVariantAttributeModel,
    ProductVariantModel,
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
        if entity.id is not None:
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
        if entity.id is not None:
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
            name=model.name,
            description=model.description,
            brand_id=model.brand_id,
            status=ProductStatus(model.status),
        )

    def to_model(self, entity: Product, model: ProductModel | None = None) -> ProductModel:
        m = model or ProductModel()
        if entity.id is not None:
            m.id = entity.id
        m.name = entity.name
        m.description = entity.description
        m.brand_id = entity.brand_id
        m.status = entity.status.value
        return m


class ProductVariantMapper(Mapper[ProductVariant, ProductVariantModel]):
    def to_entity(self, model: ProductVariantModel) -> ProductVariant:
        return ProductVariant(
            id=model.id,
            product_id=model.product_id,
            sku=model.sku,
            cost_price=model.cost_price,
            sell_price=model.sell_price,
            status=VariantStatus(model.status),
        )

    def to_model(
        self, entity: ProductVariant, model: ProductVariantModel | None = None
    ) -> ProductVariantModel:
        m = model or ProductVariantModel()
        if entity.id is not None:
            m.id = entity.id
        m.product_id = entity.product_id
        m.sku = entity.sku
        m.cost_price = entity.cost_price
        m.sell_price = entity.sell_price
        m.status = entity.status.value
        return m


class ProductCategoryMapper(Mapper[ProductCategory, ProductCategoryModel]):
    def to_entity(self, model: ProductCategoryModel) -> ProductCategory:
        return ProductCategory(
            id=model.id,
            product_id=model.product_id,
            category_id=model.category_id,
        )

    def to_model(
        self, entity: ProductCategory, model: ProductCategoryModel | None = None
    ) -> ProductCategoryModel:
        m = model or ProductCategoryModel()
        if entity.id is not None:
            m.id = entity.id
        m.product_id = entity.product_id
        m.category_id = entity.category_id
        return m


class ProductImageMapper(Mapper[ProductImage, ProductImageModel]):
    def to_entity(self, model: ProductImageModel) -> ProductImage:
        return ProductImage(
            id=model.id,
            variant_id=model.variant_id,
            file_path=model.file_path,
            order=model.order,
        )

    def to_model(
        self, entity: ProductImage, model: ProductImageModel | None = None
    ) -> ProductImageModel:
        m = model or ProductImageModel()
        if entity.id is not None:
            m.id = entity.id
        m.variant_id = entity.variant_id
        m.file_path = entity.file_path
        m.order = entity.order
        return m


class AttributeMapper(Mapper[Attribute, AttributeModel]):
    def to_entity(self, model: AttributeModel) -> Attribute:
        return Attribute(id=model.id, name=model.name)

    def to_model(self, entity: Attribute, model: AttributeModel | None = None) -> AttributeModel:
        m = model or AttributeModel()
        if entity.id is not None:
            m.id = entity.id
        m.name = entity.name
        return m


class AttributeValueMapper(Mapper[AttributeValue, AttributeValueModel]):
    def to_entity(self, model: AttributeValueModel) -> AttributeValue:
        return AttributeValue(
            id=model.id,
            attribute_id=model.attribute_id,
            value=model.value,
        )

    def to_model(
        self, entity: AttributeValue, model: AttributeValueModel | None = None
    ) -> AttributeValueModel:
        m = model or AttributeValueModel()
        if entity.id is not None:
            m.id = entity.id
        m.attribute_id = entity.attribute_id
        m.value = entity.value
        return m


class ProductVariantAttributeMapper(Mapper[ProductVariantAttribute, ProductVariantAttributeModel]):
    def to_entity(self, model: ProductVariantAttributeModel) -> ProductVariantAttribute:
        return ProductVariantAttribute(
            id=model.id,
            variant_id=model.variant_id,
            attribute_id=model.attribute_id,
            attribute_value_id=model.attribute_value_id,
        )

    def to_model(
        self,
        entity: ProductVariantAttribute,
        model: ProductVariantAttributeModel | None = None,
    ) -> ProductVariantAttributeModel:
        m = model or ProductVariantAttributeModel()
        if entity.id is not None:
            m.id = entity.id
        m.variant_id = entity.variant_id
        m.attribute_id = entity.attribute_id
        m.attribute_value_id = entity.attribute_value_id
        return m
