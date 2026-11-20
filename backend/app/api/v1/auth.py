"""Health and authentication endpoints."""

from __future__ import annotations

from flask import request
from flask_jwt_extended import jwt_required
from sqlalchemy import text

from app.api.v1.blueprint import TAG_AUTH, TAG_HEALTH, api_v1
from app.api.v1.deps import current_user
from app.api.v1.schemas import (
    ChangePasswordBody,
    LoginBody,
    OrganizationBody,
    ProfileBody,
    RegisterBody,
    UpdateMeBody,
)
from app.core.db import db
from app.core.errors import ApiError, success
from app.core.rate_limit import login_limiter
from app.modules.auth import service


@api_v1.get("/health", tags=[TAG_HEALTH], summary="Service health")
def health():
    database = "ok"
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        database = "error"
    return success(
        {
            "status": "ok" if database == "ok" else "degraded",
            "database": database,
            "version": "1.0.0",
            "ai_model": "openrouter/free",
        }
    )


@api_v1.post("/auth/register", tags=[TAG_AUTH], summary="Create an account")
def register(body: RegisterBody):
    data = service.register_user(body)
    return success(data, 201)


@api_v1.post("/auth/login", tags=[TAG_AUTH], summary="Log in")
def login(body: LoginBody):
    login_limiter.check(f"login:{service.request_ip()}:{body.email}".lower())
    data = service.login_user(body)
    login_limiter.reset(f"login:{service.request_ip()}:{body.email}".lower())
    return success(data)


@api_v1.post("/auth/refresh", tags=[TAG_AUTH], summary="Rotate refresh token")
@jwt_required(refresh=True)
def refresh():
    return success(service.refresh_tokens())


@api_v1.post("/auth/logout", tags=[TAG_AUTH], summary="Revoke refresh token(s)")
@jwt_required()
def logout():
    user = current_user()
    payload = request.get_json(silent=True) or {}
    raw_token = payload.get("refresh_token")
    all_devices = bool(payload.get("all_devices", False))
    if raw_token is not None and not isinstance(raw_token, str):
        raise ApiError("validation_error", "refresh_token must be a string.", 422)
    service.revoke_refresh_token(raw_token, user, all_devices=all_devices)
    return success({"logged_out": True})


@api_v1.get("/auth/me", tags=[TAG_AUTH], summary="Current user and profile")
@jwt_required()
def me():
    user = current_user()
    profile = service.profile_payload(user)
    org = user.organization.to_dict() if user.organization else None
    return success({"user": user.to_dict(), "profile": profile, "organization": org})


@api_v1.patch("/auth/me", tags=[TAG_AUTH], summary="Update name, locale, timezone")
@jwt_required()
def update_me(body: UpdateMeBody):
    user = current_user()
    return success(service.update_me(user, body))


@api_v1.patch("/auth/password", tags=[TAG_AUTH], summary="Change password")
@jwt_required()
def change_password(body: ChangePasswordBody):
    user = current_user()
    service.change_password(user, body)
    return success({"updated": True})


@api_v1.get("/profile", tags=[TAG_AUTH], summary="Profile detail")
@jwt_required()
def get_profile():
    return success(service.profile_payload(current_user()))


@api_v1.patch("/profile", tags=[TAG_AUTH], summary="Update profile and preferences")
@jwt_required()
def update_profile(body: ProfileBody):
    return success(service.update_profile(current_user(), body))


@api_v1.get("/organization", tags=[TAG_AUTH], summary="Organization detail")
@jwt_required()
def get_organization():
    return success(service.organization_payload(current_user()))


@api_v1.patch("/organization", tags=[TAG_AUTH], summary="Update organization")
@jwt_required()
def update_organization(body: OrganizationBody):
    return success(service.update_organization(current_user(), body))
