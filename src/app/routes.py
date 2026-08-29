from flask import Flask

from src.domains.accounts.routes.v1 import router as accounts_v1
from src.domains.auth.routes.v1 import router as auth_v1
from src.domains.rbac.routes.v1 import router as rbac_router
from src.domains.catalog.routes.v1 import router as catalog_router
from src.domains.sale.routes.v1.sale_routes import sale_bp
from src.domains.sale.routes.v1.refund_routes import refund_bp
from src.domains.stock.routes.v1 import router as stock_router
from src.domains.billing.routes.v1.payment_routes import payments_bp
from src.domains.billing.routes.v1.payment_method_routes import payment_methods_bp


def register_routes(app: Flask) -> None:
    app.register_blueprint(accounts_v1, url_prefix="/api/v1")
    app.register_blueprint(auth_v1, url_prefix="/api/v1")
    app.register_blueprint(rbac_router, url_prefix="/api/v1")
    app.register_blueprint(catalog_router, url_prefix="/api/v1")
    app.register_blueprint(sale_bp)
    app.register_blueprint(refund_bp)
    app.register_blueprint(stock_router, url_prefix="/api/v1/stock")
    app.register_blueprint(payments_bp)
    app.register_blueprint(payment_methods_bp)
