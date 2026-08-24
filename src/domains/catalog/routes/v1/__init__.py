"""Catalog v1 routes — /api/v1/categories, /api/v1/brands, /api/v1/products, /api/v1/variants, /api/v1/attributes"""
from __future__ import annotations

from flask import Blueprint

from .attribute_routes import bp as attribute_bp
from .brand_routes import bp as brand_bp
from .category_routes import bp as category_bp
from .product_routes import bp as product_bp
from .product_variant_routes import bp as variant_bp

router = Blueprint("catalog", __name__)

router.register_blueprint(category_bp, url_prefix="/categories")
router.register_blueprint(brand_bp, url_prefix="/brands")
router.register_blueprint(product_bp, url_prefix="/products")
router.register_blueprint(variant_bp, url_prefix="/variants")
router.register_blueprint(attribute_bp, url_prefix="/attributes")
