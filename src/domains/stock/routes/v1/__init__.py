"""Stock blueprint registration."""
from flask import Blueprint

from .stock_item_routes import bp as item_bp
from .stock_movement_routes import bp as movement_bp

router = Blueprint("stock_v1", __name__)

router.register_blueprint(item_bp, url_prefix="/items")
router.register_blueprint(movement_bp, url_prefix="/movements")
