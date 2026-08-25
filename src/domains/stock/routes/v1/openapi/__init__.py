from src.domains.stock.routes.v1.openapi.stock_item_openapi import register_stock_item_docs
from src.domains.stock.routes.v1.openapi.stock_movement_openapi import register_stock_movement_docs

def register() -> None:
    register_stock_item_docs()
    register_stock_movement_docs()
