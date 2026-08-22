"""API tests for Catalog domain."""
from __future__ import annotations

import io
import uuid

import pytest
from flask_jwt_extended import create_access_token


@pytest.fixture
def catalog_superuser_headers(app):
    with app.app_context():
        domain_service = app.extensions["domain_service"]
        from tests.conftest import MockActor
        mock_actor = MockActor({"*"})
        unique_suffix = uuid.uuid4().hex[:8]
        
        acc = domain_service.accounts.account.create_account("Admin", "Catalog").data
        
        role_res = domain_service.rbac.role.create_role(
            mock_actor, f"catalog_admin_{acc.id}_{unique_suffix}", "Catalog Admin"
        ).data
        domain_service.accounts.account_role.assign_role(mock_actor, acc.id, role_res.id)
        
        # Grant permissions for catalog
        for entity in ["brand", "category", "product", "product_image"]:
            for action in ["create", "read", "update", "delete", "list"]:
                resource_name = f"catalog:{entity}"
                from src.domains.rbac.exceptions import PermissionAlreadyExists
                try:
                    perm = domain_service.rbac.permission.create_permission(
                        mock_actor, resource_name, action, "All perms"
                    ).data
                except PermissionAlreadyExists:
                    from src.domains.rbac.repositories.filters import PermissionFilter
                    with domain_service.rbac.permission._uow_factory() as uow:
                        res = uow.permissions.list(PermissionFilter(resource=resource_name, action=action))
                        perm = res.items[0]
                domain_service.rbac.role_permission.assign(mock_actor, role_res.id, perm.id)

        token = create_access_token(identity=str(acc.id))
        return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def normal_user_headers(app):
    with app.app_context():
        domain_service = app.extensions["domain_service"]
        acc = domain_service.accounts.account.create_account("Normal", "User").data
        token = create_access_token(identity=str(acc.id))
        return {"Authorization": f"Bearer {token}"}


def test_brand_api(client, catalog_superuser_headers, normal_user_headers):
    # Unauthenticated
    res = client.post("/api/v1/brands", json={"name": "Sony", "description": "Tech"})
    assert res.status_code == 401

    # Forbidden
    res = client.post("/api/v1/brands", headers=normal_user_headers, json={"name": "Sony"})
    assert res.status_code == 403

    # Create Brand
    res = client.post("/api/v1/brands", headers=catalog_superuser_headers, json={
        "name": "Sony", "description": "Tech"
    })
    assert res.status_code == 201
    brand_id = res.get_json()["data"]["id"]

    # Get Brand
    res = client.get(f"/api/v1/brands/{brand_id}", headers=catalog_superuser_headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["name"] == "Sony"

    # List Brands
    res = client.get("/api/v1/brands", headers=catalog_superuser_headers)
    assert res.status_code == 200
    assert len(res.get_json()["data"]) >= 1

    # Update Brand
    res = client.put(f"/api/v1/brands/{brand_id}", headers=catalog_superuser_headers, json={
        "name": "Sony",
        "description": "Sony Tech"
    })
    assert res.status_code == 200
    assert res.get_json()["data"]["description"] == "Sony Tech"

    # Upload Logo
    data = {
        'file': (io.BytesIO(b"logo"), 'logo.png')
    }
    res = client.post(f"/api/v1/brands/{brand_id}/logo", headers=catalog_superuser_headers, data=data, content_type='multipart/form-data')
    assert res.status_code == 200
    
    # Delete Logo
    res = client.delete(f"/api/v1/brands/{brand_id}/logo", headers=catalog_superuser_headers)
    assert res.status_code == 200

    # Delete Brand
    res = client.delete(f"/api/v1/brands/{brand_id}", headers=catalog_superuser_headers)
    assert res.status_code == 200


def test_category_api(client, catalog_superuser_headers):
    # Create Category
    res = client.post("/api/v1/categories", headers=catalog_superuser_headers, json={
        "name": "Books"
    })
    assert res.status_code == 201
    cat_id = res.get_json()["data"]["id"]

    # Get Category
    res = client.get(f"/api/v1/categories/{cat_id}", headers=catalog_superuser_headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["name"] == "Books"

    # List Categories
    res = client.get("/api/v1/categories", headers=catalog_superuser_headers)
    assert res.status_code == 200
    assert len(res.get_json()["data"]) >= 1

    # Update Category
    res = client.put(f"/api/v1/categories/{cat_id}", headers=catalog_superuser_headers, json={
        "name": "Updated Books"
    })
    assert res.status_code == 200
    assert res.get_json()["data"]["name"] == "Updated Books"

    # Delete Category
    res = client.delete(f"/api/v1/categories/{cat_id}", headers=catalog_superuser_headers)
    assert res.status_code == 200


def test_product_api(client, catalog_superuser_headers):
    # Setup brand & category
    brand_res = client.post("/api/v1/brands", headers=catalog_superuser_headers, json={"name": "Dell"})
    brand_id = brand_res.get_json()["data"]["id"]

    cat_res = client.post("/api/v1/categories", headers=catalog_superuser_headers, json={"name": "Laptops"})
    cat_id = cat_res.get_json()["data"]["id"]

    # Create Product
    res = client.post("/api/v1/products", headers=catalog_superuser_headers, json={
        "sku": "DELL-XPS-15",
        "name": "Dell XPS 15",
        "cost_price": 100000,
        "sell_price": 149999,
        "brand_id": brand_id,
        "category_id": cat_id
    })
    assert res.status_code == 201
    prod_id = res.get_json()["data"]["id"]

    # Get Product
    res = client.get(f"/api/v1/products/{prod_id}", headers=catalog_superuser_headers)
    assert res.status_code == 200

    # List Products
    res = client.get("/api/v1/products", headers=catalog_superuser_headers)
    assert res.status_code == 200
    assert len(res.get_json()["data"]) >= 1

    # Update Product
    res = client.put(f"/api/v1/products/{prod_id}", headers=catalog_superuser_headers, json={
        "sku": "DELL-XPS-15",
        "name": "Dell XPS 15",
        "cost_price": 90000,
        "sell_price": 129999
    })
    assert res.status_code == 200
    assert res.get_json()["data"]["sell_price"] == 129999

    # Upload Image
    data = {'file': (io.BytesIO(b"img"), 'img.png')}
    res = client.post(f"/api/v1/products/{prod_id}/images", headers=catalog_superuser_headers, data=data, content_type='multipart/form-data')
    assert res.status_code == 201
    img_id = res.get_json()["data"]["id"]

    # List Images
    res = client.get(f"/api/v1/products/{prod_id}/images", headers=catalog_superuser_headers)
    assert res.status_code == 200
    assert len(res.get_json()["data"]) == 1

    # Set Primary
    res = client.put(f"/api/v1/products/{prod_id}/images/{img_id}/primary", headers=catalog_superuser_headers)
    assert res.status_code == 200

    # Delete Image
    res = client.delete(f"/api/v1/products/{prod_id}/images/{img_id}", headers=catalog_superuser_headers)
    assert res.status_code == 200

    # Delete Product
    res = client.delete(f"/api/v1/products/{prod_id}", headers=catalog_superuser_headers)
    assert res.status_code == 200
