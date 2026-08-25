from flask import Flask

def register_routes(app: Flask) -> None:
    # We will import and register the blueprints here after refactoring them
    try:
        from src.domains.accounts.routes.v1 import router as accounts_v1
        app.register_blueprint(accounts_v1, url_prefix="/api/v1")
    except ImportError:
        pass
    
    try:
        from src.domains.auth.routes.v1 import router as auth_v1
        app.register_blueprint(auth_v1, url_prefix="/api/v1")
    except ImportError:
        pass
        
    try:
        from src.domains.rbac.routes.v1 import router as rbac_router
        app.register_blueprint(rbac_router, url_prefix="/api/v1")
    except ImportError:
        pass
        
    try:
        from src.domains.catalog.routes.v1 import router as catalog_router
        app.register_blueprint(catalog_router, url_prefix="/api/v1")
    except ImportError:
        pass

    from src.domains.sale.routes.v1.sale_routes import sale_bp
    from src.domains.sale.routes.v1.refund_routes import refund_bp
    app.register_blueprint(sale_bp)
    app.register_blueprint(refund_bp)

    try:
        from src.domains.stock.routes.v1 import router as stock_router
        app.register_blueprint(stock_router, url_prefix="/api/v1/stock")
    except ImportError:
        pass
