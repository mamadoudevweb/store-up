"""Products v1 routes — /api/v1/categories, /api/v1/brands, /api/v1/products"""
from __future__ import annotations

from flask import Blueprint

from .brand_routes import bp as brand_bp
from .category_routes import bp as category_bp
from .product_routes import bp as product_bp

router = Blueprint("products", __name__)

router.register_blueprint(category_bp, url_prefix="/categories")
router.register_blueprint(brand_bp, url_prefix="/brands")
router.register_blueprint(product_bp, url_prefix="/products")
