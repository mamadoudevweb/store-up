from flask import Flask

def register_openapi(app: Flask) -> None:
    try:
        from src.domains.accounts.routes.v1 import openapi as account_openapi
        account_openapi.register()
    except ImportError:
        pass
        
    try:
        from src.domains.auth.routes.v1 import openapi as auth_openapi
        auth_openapi.register()
    except ImportError:
        pass
    try:
        from src.domains.rbac.routes.v1 import openapi as rbac_openapi
        rbac_openapi.register()
    except ImportError:
        pass
        
    try:
        from src.domains.sale.routes.v1 import openapi as sale_openapi
        sale_openapi.register()
    except ImportError:
        pass
        
    try:
        from src.domains.catalog.routes.v1 import openapi as catalog_openapi
        catalog_openapi.register()
    except ImportError:
        pass
        
    from src.core.docs.docs_blueprint import bp as docs_bp
    app.register_blueprint(docs_bp)
