"""Consistent API errors and response envelopes."""

from __future__ import annotations

from typing import Any

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    """A typed domain error that maps to the API error envelope."""

    def __init__(
        self,
        code: str,
        message: str,
        status: int = 400,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details or {}


def success(data: Any, status: int = 200):
    return jsonify({"data": data}), status


def error_response(
    code: str,
    message: str,
    status: int = 400,
    details: Any | None = None,
):
    return (
        jsonify(
            {
                "error": {
                    "code": code,
                    "message": message,
                    "details": details or {},
                }
            }
        ),
        status,
    )


def validation_error_callback(error: Any):
    """Callback used by flask-openapi3 for pydantic validation errors.

    Pydantic's ValidationError is not JSON serializable, so expose a small,
    stable subset of each issue (location, message, type).
    """
    details = []
    try:
        raw_errors = error.errors(include_url=False)
    except (AttributeError, TypeError):
        raw_errors = []
    for item in raw_errors:
        details.append(
            {
                "loc": [str(part) for part in item.get("loc", [])],
                "msg": item.get("msg", "Invalid value"),
                "type": item.get("type", "value_error"),
            }
        )
    response, status = error_response("validation_error", "Invalid input", 422, details)
    response.status_code = status
    return response


def _wants_json() -> bool:
    return request.path.startswith("/api") or request.accept_mimetypes.best == "application/json"


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(exc: ApiError):
        if _wants_json():
            return error_response(exc.code, exc.message, exc.status, exc.details)
        return (
            render_template("errors/error.html", code=exc.status, message=exc.message),
            exc.status,
        )

    @app.errorhandler(HTTPException)
    def handle_http_error(exc: HTTPException):
        code_map = {
            400: "bad_request",
            401: "unauthorized",
            403: "forbidden",
            404: "not_found",
            405: "method_not_allowed",
            413: "upload_too_large",
        }
        code = code_map.get(exc.code or 500, "http_error")
        message = exc.description or "Request failed"
        if _wants_json():
            return error_response(code, message, exc.code or 500)
        return (
            render_template("errors/error.html", code=exc.code or 500, message=message),
            exc.code or 500,
        )

    @app.errorhandler(413)
    def handle_too_large(exc):  # noqa: ANN001
        if _wants_json():
            return error_response(
                "upload_too_large",
                "The uploaded file or request is too large.",
                413,
            )
        return render_template("errors/error.html", code=413, message="Upload too large"), 413

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception):
        app.logger.exception("Unhandled error: %s", exc.__class__.__name__)
        if _wants_json():
            return error_response("internal_error", "An unexpected error occurred.", 500)
        return (
            render_template(
                "errors/error.html",
                code=500,
                message="An unexpected error occurred.",
            ),
            500,
        )
