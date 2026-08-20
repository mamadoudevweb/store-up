from typing import Any
from flask import Flask

class DomainService:
    """Aggregates every domain's DomainService. core/ and this class don't
    know the domain names in advance — the composition root supplies them."""

    def __init__(self, **domains: Any) -> None:
        self.__dict__.update(domains)

    def init_app(self, app: Flask) -> None:
        app.extensions["domain_service"] = self
