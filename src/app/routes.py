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
