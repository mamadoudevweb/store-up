from flask import Blueprint, Response, jsonify, render_template_string
from src.core.docs.openapi_registry import spec

bp = Blueprint("docs", __name__, url_prefix="/api/v1")

SWAGGER_UI_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Store-Up API Docs</title>
    <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css" >
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"> </script>
    <script>
      window.onload = function() {
        SwaggerUIBundle({
          url: "{{ spec_url }}",
          dom_id: '#swagger-ui',
        })
      }
    </script>
</body>
</html>
"""

@bp.get("/openapi.json")
def openapi_json() -> Response:
    return jsonify(spec.to_dict())

@bp.get("/docs")
def swagger_ui() -> str:
    return render_template_string(SWAGGER_UI_TEMPLATE, spec_url="/api/v1/openapi.json")
