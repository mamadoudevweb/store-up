from src.domains.catalog.routes.v1.openapi.brand_openapi import register_brand_docs
from src.domains.catalog.routes.v1.openapi.category_openapi import register_category_docs
from src.domains.catalog.routes.v1.openapi.attribute_openapi import register_attribute_docs
from src.domains.catalog.routes.v1.openapi.product_openapi import register_product_docs
from src.domains.catalog.routes.v1.openapi.product_variant_openapi import register_variant_docs

def register() -> None:
    register_brand_docs()
    register_category_docs()
    register_attribute_docs()
    register_product_docs()
    register_variant_docs()
