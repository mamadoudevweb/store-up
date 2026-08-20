from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin

spec = APISpec(
    title="Store-Up API",
    version="1.0.0",
    openapi_version="3.0.3",
    info={"description": "Store Management API"},
    plugins=[MarshmallowPlugin()],
)
