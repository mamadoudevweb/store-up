from flask import Flask
from pydantic import ValidationError as PydanticValidationError
from src.core.services.errors import AppError
from src.core.routes.envelope import fail, EnvelopeResponse
from werkzeug.exceptions import HTTPException

def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(err: AppError) -> EnvelopeResponse:
        return fail(err.code, err.message, err.status_code, err.details)

    @app.errorhandler(PydanticValidationError)
    def handle_validation_error(err: PydanticValidationError) -> EnvelopeResponse:
        return fail("VALIDATION_ERROR", "Invalid request data", 422, {"errors": err.errors()})

    @app.errorhandler(404)
    def handle_404(err: Exception) -> EnvelopeResponse:
        return fail("NOT_FOUND", "Resource not found", 404)

    @app.errorhandler(429)
    def handle_rate_limited(err: Exception) -> EnvelopeResponse:
        return fail("RATE_LIMITED", "Too many requests", 429)

    @app.errorhandler(HTTPException)
    def handle_http_error(err: HTTPException) -> EnvelopeResponse:
        code = err.name.upper().replace(" ", "_") if err.name else "HTTP_ERROR"
        return fail(code, err.description or "HTTP Error", err.code or 500)

    @app.errorhandler(Exception)
    def handle_unexpected(err: Exception) -> EnvelopeResponse:
        app.logger.exception(err)
        return fail("INTERNAL_ERROR", "Something went wrong", 500)
