"""Integration tests for Catalog domain services."""
from __future__ import annotations

import io
import uuid

import pytest

from src.domains.catalog.exceptions import (
    BrandNotFound, CategoryNotFound,
    ProductNotFound, DuplicateSkuError, ProductImageNotFound
)

@pytest.fixture
def catalog_service(app):
    with app.app_context():
        yield app.extensions["domain_service"].catalog

def test_brand_service(catalog_service, mock_actor):
    # Create brand
    res = catalog_service.brand.create_brand(mock_actor, name="Apple", description="Tech")
    assert res.success
    brand_id = res.data.id

    # The brand service does not check for uniqueness by name (or we don't have an exception for it)

    # Get brand
    res = catalog_service.brand.get_brand(mock_actor, brand_id)
    assert res.data.name == "Apple"
    assert res.data.description == "Tech"

    # Get non-existent
    with pytest.raises(BrandNotFound):
        catalog_service.brand.get_brand(mock_actor, uuid.uuid4())

    # Update brand
    res = catalog_service.brand.update_brand(mock_actor, brand_id, name="Apple Inc", description="New tech")
    assert res.data.description == "New tech"
    assert res.data.name == "Apple Inc"

    # List brands
    from src.domains.catalog.repositories.filters import BrandFilter
    res = catalog_service.brand.list_brands(mock_actor, BrandFilter())
    assert len(res.data.items) >= 1

    # Upload logo
    fake_file = io.BytesIO(b"fake image data")
    fake_file.filename = "logo.png"
    fake_file.content_type = "image/png"
    res = catalog_service.brand.upload_logo(mock_actor, brand_id, fake_file)
    assert res.success
    assert "logo" in res.data.logo_url

    # Delete logo
    res = catalog_service.brand.delete_logo(mock_actor, brand_id)
    assert res.success
    assert res.data.logo_url is None

    # Delete brand
    res = catalog_service.brand.delete_brand(mock_actor, brand_id)
    assert res.success
    
    with pytest.raises(BrandNotFound):
        catalog_service.brand.get_brand(mock_actor, brand_id)

def test_category_service(catalog_service, mock_actor):
    # Create category
    res = catalog_service.category.create_category(mock_actor, name="Electronics", description="Gadgets")
    assert res.success
    category_id = res.data.id

    # Category uniqueness isn't explicitly enforced with an exception in the domain

    # Update category
    res = catalog_service.category.update_category(mock_actor, category_id, name="Electronic devices")
    assert res.success
    assert res.data.name == "Electronic devices"

    # Create child category
    res_child = catalog_service.category.create_category(mock_actor, name="Phones", parent_id=category_id)
    assert res_child.success
    assert res_child.data.parent_id == category_id

    # Get category
    res = catalog_service.category.get_category(mock_actor, category_id)
    assert res.data.name == "Electronics"
    with pytest.raises(CategoryNotFound):
        catalog_service.category.get_category(mock_actor, uuid.uuid4())

    # List categories
    from src.domains.catalog.repositories.filters import CategoryFilter
    res = catalog_service.category.list_categories(mock_actor, CategoryFilter())
    assert len(res.data.items) >= 2

    # Delete child category
    catalog_service.category.delete_category(mock_actor, res_child.data.id)

    # Delete category
    catalog_service.category.delete_category(mock_actor, category_id)
    with pytest.raises(CategoryNotFound):
        catalog_service.category.get_category(mock_actor, category_id)

def test_product_service(catalog_service, mock_actor):
    # Setup brand and category
    brand = catalog_service.brand.create_brand(mock_actor, name="Samsung").data
    category = catalog_service.category.create_category(mock_actor, name="TVs").data

    # Create product
    res = catalog_service.product.create_product(
        mock_actor,
        sku="TV-001",
        name="Smart TV",
        cost_price=40000,
        sell_price=59999,
        brand_id=brand.id,
        category_id=category.id
    )
    assert res.success
    product_id = res.data.id
    assert res.data.sku == "TV-001"

    # Duplicate sku
    with pytest.raises(DuplicateSkuError):
        catalog_service.product.create_product(mock_actor, sku="TV-001", name="Smart TV 2", cost_price=100, sell_price=200, brand_id=brand.id, category_id=category.id)

    # Get product
    res = catalog_service.product.get_product(mock_actor, product_id)
    assert res.data.name == "Smart TV"

    with pytest.raises(ProductNotFound):
        catalog_service.product.get_product(mock_actor, uuid.uuid4())

    # Update product
    res = catalog_service.product.update_product(mock_actor, product_id, sku="TV-001", name="Smart TV", cost_price=30000, sell_price=49999)
    assert res.data.sell_price == 49999

    # List products
    from src.domains.catalog.repositories.filters import ProductFilter
    res = catalog_service.product.list_products(mock_actor, ProductFilter())
    assert len(res.data.items) >= 1

    # Product Images
    fake_img = io.BytesIO(b"img data")
    fake_img.filename = "tv.jpg"
    fake_img.content_type = "image/jpeg"

    # Upload image
    img_res = catalog_service.product_image.upload_image(mock_actor, product_id, fake_img, is_primary=True)
    assert img_res.success
    img_id = img_res.data.id

    # List images
    imgs = catalog_service.product_image.list_images(mock_actor, product_id).data
    assert len(imgs) == 1
    assert imgs[0].is_primary is True

    # Upload second image
    fake_img2 = io.BytesIO(b"img2 data")
    fake_img2.filename = "tv2.jpg"
    fake_img2.content_type = "image/jpeg"
    img_res2 = catalog_service.product_image.upload_image(mock_actor, product_id, fake_img2, is_primary=False)

    # Set primary
    catalog_service.product_image.set_primary(mock_actor, img_res2.data.id)
    imgs2 = catalog_service.product_image.list_images(mock_actor, product_id).data
    primary_imgs = [i for i in imgs2 if i.is_primary]
    assert len(primary_imgs) == 1
    assert primary_imgs[0].id == img_res2.data.id

    # Delete image
    catalog_service.product_image.delete_image(mock_actor, img_id)
    imgs_after = catalog_service.product_image.list_images(mock_actor, product_id).data
    assert len(imgs_after) == 1

    with pytest.raises(ProductImageNotFound):
        catalog_service.product_image.delete_image(mock_actor, img_id)

    # Delete product
    catalog_service.product.delete_product(mock_actor, product_id)
    with pytest.raises(ProductNotFound):
        catalog_service.product.get_product(mock_actor, product_id)
