"""CarbonWise Flask application factory."""

from __future__ import annotations

from flask import Flask, jsonify, redirect, url_for
from flask_openapi3 import Info, OpenAPI, SecurityScheme

from app.core.config import Config
from app.core.db import db
from app.core.errors import error_response, register_error_handlers, validation_error_callback
from app.core.extensions import csrf, jwt, migrate
from app.modules.ai.errors import AiUnavailable


@jwt.unauthorized_loader
def _missing_token(reason: str):
    return error_response("unauthorized", "Authentication is required.", 401)


@jwt.invalid_token_loader
def _invalid_token(reason: str):
    return error_response("invalid_token", "The token is invalid.", 401)


@jwt.expired_token_loader
def _expired_token(header, payload):  # noqa: ANN001
    token_type = payload.get("type", "access")
    return error_response(
        "token_expired",
        f"The {token_type} token has expired.",
        401,
    )


@jwt.revoked_token_loader
def _revoked_token(header, payload):  # noqa: ANN001
    return error_response("token_revoked", "The token has been revoked.", 401)


@jwt.needs_fresh_token_loader
def _fresh_token_required(header, payload):  # noqa: ANN001
    return error_response("fresh_token_required", "A fresh token is required.", 401)


@jwt.user_lookup_loader
def _user_lookup(_jwt_header, jwt_data):  # noqa: ANN001
    from app.modules.users.models import User

    identity = jwt_data.get("sub")
    try:
        return db.session.get(User, int(identity))
    except (TypeError, ValueError):
        return None


def create_app(config_object: type = Config) -> Flask:
    app = OpenAPI(
        __name__,
        info=Info(
            title="CarbonWise API",
            version="1.0.0",
            description=(
                "AI-assisted carbon footprint tracking for individuals, households, "
                "and organizations. Every emission value is calculated by the backend; "
                "AI explains and recommends but never invents numbers."
            ),
        ),
        security_schemes={
            "bearerAuth": SecurityScheme(
                type="http",
                scheme="bearer",
                bearerFormat="JWT",
                description="Access token from /api/v1/auth/login",
            )
        },
        validation_error_callback=validation_error_callback,
        doc_prefix="/api",
        doc_url="/api/openapi.json",
        static_folder="static",
        template_folder="templates",
    )
    app.config.from_object(config_object)
    app.json.sort_keys = False

    if hasattr(config_object, "init_app"):
        config_object.init_app(app)

    db.init_app(app)
    jwt.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)

    register_error_handlers(app)

    @app.errorhandler(AiUnavailable)
    def handle_ai_unavailable(exc: AiUnavailable):
        return error_response(exc.code, exc.message, exc.status, exc.details)

    # Importing models registers all tables on db.metadata.
    from app import models  # noqa: F401
    from app.api.v1 import api_v1

    app.register_api(api_v1)
    csrf.exempt(api_v1)

    from app.modules.admin.routes import admin_bp

    app.register_blueprint(admin_bp)

    from app.cli import register_cli

    register_cli(app)

    @app.get("/")
    def root():
        return redirect(url_for("admin.login"))

    @app.get("/favicon.ico")
    def favicon():
        return app.send_static_file("assets/images/favicon.png") if app.static_folder else ("", 404)

    @app.get("/health")
    def health_root():
        return jsonify({"status": "ok", "service": "carbonwise-api"})

    return app
