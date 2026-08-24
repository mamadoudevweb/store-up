import uuid
import pytest

@pytest.fixture
def test_variant_id(app, mock_actor):
    with app.app_context():
        domain_service = app.extensions["domain_service"]
        
        brand_id = domain_service.catalog.brand.create_brand(mock_actor, name="Test Brand").data.id
        cat_id = domain_service.catalog.category.create_category(mock_actor, name="Test Category").data.id
        prod_res = domain_service.catalog.product.create_product(
            mock_actor,
            name="Test Product",
            sku=f"TEST-SKU-{uuid.uuid4()}",
            cost_price=100,
            sell_price=500,
            brand_id=brand_id
        ).data
        from src.domains.catalog.repositories.filters import ProductVariantFilter
        variant_page = domain_service.catalog.variant.list_variants(mock_actor, ProductVariantFilter(product_id=prod_res.id)).data
        variant_id = str(variant_page.items[0].id)
        
        from src.domains.stock.entities.enums import StockMovementReason, ReferenceType
        domain_service.stock.item.adjust_stock(
            mock_actor,
            variant_id=uuid.UUID(variant_id),
            quantity_change=10,
            reason=StockMovementReason.RESTOCK,
            reference_type=ReferenceType.MANUAL_ADJUSTMENT,
            reference_id="Initial stock"
        )
        return variant_id
