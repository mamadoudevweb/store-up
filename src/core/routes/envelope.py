from typing import Any
from pydantic import BaseModel

class Envelope(BaseModel):
    success: bool
    data: Any | None = None
    error: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None

EnvelopeResponse = tuple[dict[str, Any], int]   # what every route/handler returns

def ok(data: Any = None, meta: dict[str, Any] | None = None, status: int = 200) -> EnvelopeResponse:
    return Envelope(success=True, data=data, meta=meta).model_dump(mode="json"), status

def fail(code: str, message: str, status: int, details: dict[str, Any] | None = None) -> EnvelopeResponse:
    return Envelope(success=False, error={"code": code, "message": message, "details": details}).model_dump(mode="json"), status
