"""Authentication and profile service."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from flask import request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_jwt,
)

from app.core.db import db, utcnow
from app.core.errors import ApiError
from app.core.security import hash_password, verify_password
from app.core.text import unique_slug
from app.core.validators import (
    clean_account_type,
    clean_email,
    clean_locale,
    clean_password,
    clean_timezone,
)
from app.modules.organizations.models import Organization
from app.modules.users.models import RefreshToken, User, UserProfile


def hash_jti(jti: str) -> str:
    return hashlib.sha256(jti.encode("utf-8")).hexdigest()


def _expires_at(token: str) -> datetime:
    payload = decode_token(token)
    return datetime.fromtimestamp(payload["exp"], tz=UTC).replace(tzinfo=None)


def issue_tokens(user: User) -> dict:
    access = create_access_token(
        identity=str(user.id),
        additional_claims={"type": "access", "email": user.email},
    )
    refresh = create_refresh_token(
        identity=str(user.id),
        additional_claims={"type": "refresh", "email": user.email},
    )
    refresh_payload = decode_token(refresh)
    db.session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_jti(refresh_payload["jti"]),
            expires_at=_expires_at(refresh),
            created_at=utcnow(),
        )
    )
    db.session.commit()
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "Bearer",
        "expires_in": 30 * 60,
    }


def token_envelope(user: User) -> dict:
    tokens = issue_tokens(user)
    return {"user": user.to_dict(), **tokens}


def register_user(payload) -> dict:
    email = clean_email(str(payload.email))
    password = clean_password(payload.password)
    account_type = clean_account_type(payload.account_type)
    locale = clean_locale(payload.locale)
    timezone = clean_timezone(payload.timezone)
    full_name = payload.full_name.strip()

    if User.query.filter_by(email=email).first():
        raise ApiError("conflict", "An account with this email already exists.", 409)

    organization = None
    if account_type == "organization":
        name = (payload.organization_name or "").strip()
        if len(name) < 2:
            raise ApiError(
                "validation_error",
                "organization_name is required for organization accounts.",
                422,
            )
        organization = Organization(
            name_en=name,
            name_ar=name,
            slug=unique_slug(Organization, name),
            org_type="business",
            contact_email=email,
        )
        db.session.add(organization)
        db.session.flush()

    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        account_type=account_type,
        organization_id=organization.id if organization else None,
        is_org_owner=account_type == "organization",
        locale=locale,
        timezone=timezone,
    )
    db.session.add(user)
    db.session.flush()

    profile = UserProfile(
        user_id=user.id,
        household_size=payload.household_size,
        onboarding_completed=False,
        leaderboard_opt_in=False,
    )
    db.session.add(profile)
    db.session.commit()
    return token_envelope(user)


def login_user(payload) -> dict:
    email = clean_email(str(payload.email))
    user = User.query.filter_by(email=email).first()
    if not user or not verify_password(user.password_hash, payload.password):
        raise ApiError("invalid_credentials", "Email or password is incorrect.", 401)
    if not user.is_active:
        raise ApiError("account_inactive", "This account is suspended.", 403)
    user.last_login_at = utcnow()
    db.session.commit()
    return token_envelope(user)


def refresh_tokens() -> dict:
    claims = get_jwt()
    if claims.get("type") != "refresh":
        raise ApiError("invalid_token", "A refresh token is required.", 401)
    token_hash = hash_jti(claims.get("jti", ""))
    row = RefreshToken.query.filter_by(token_hash=token_hash).first()
    if row is None or row.revoked_at is not None or row.expires_at < utcnow():
        raise ApiError("token_revoked", "This refresh token is no longer valid.", 401)
    user = db.session.get(User, row.user_id)
    if user is None or not user.is_active:
        raise ApiError("account_inactive", "This account is not active.", 403)
    row.revoked_at = utcnow()
    db.session.commit()
    return token_envelope(user)


def revoke_refresh_token(raw_token: str | None, user: User, all_devices: bool = False) -> None:
    if all_devices or not raw_token:
        RefreshToken.query.filter_by(user_id=user.id, revoked_at=None).update(
            {"revoked_at": utcnow()}
        )
        db.session.commit()
        return
    try:
        payload = decode_token(raw_token)
    except Exception as exc:  # noqa: BLE001
        raise ApiError("invalid_token", "The refresh token is invalid.", 401) from exc
    if payload.get("type") != "refresh" or str(payload.get("sub")) != str(user.id):
        raise ApiError("invalid_token", "The refresh token is invalid.", 401)
    row = RefreshToken.query.filter_by(token_hash=hash_jti(payload["jti"])).first()
    if row is not None:
        row.revoked_at = utcnow()
        db.session.commit()


def update_me(user: User, payload) -> dict:
    if payload.full_name is not None:
        name = payload.full_name.strip()
        if len(name) < 2:
            raise ApiError("validation_error", "full_name is too short.", 422)
        user.full_name = name
    if payload.locale is not None:
        user.locale = clean_locale(payload.locale)
    if payload.timezone is not None:
        user.timezone = clean_timezone(payload.timezone)
    db.session.commit()
    return user.to_dict()


def change_password(user: User, payload) -> None:
    if not verify_password(user.password_hash, payload.current_password):
        raise ApiError("invalid_credentials", "Current password is incorrect.", 401)
    user.password_hash = hash_password(clean_password(payload.new_password))
    # Revoke all refresh tokens after a password change.
    RefreshToken.query.filter_by(user_id=user.id, revoked_at=None).update({"revoked_at": utcnow()})
    db.session.commit()


def profile_payload(user: User) -> dict:
    if user.profile is None:
        user.profile = UserProfile(user_id=user.id)
        db.session.commit()
    return user.profile.to_dict()


def update_profile(user: User, payload) -> dict:
    profile = user.profile or UserProfile(user_id=user.id)
    if user.profile is None:
        db.session.add(profile)
    data = payload.model_dump(exclude_unset=True)
    if "leaderboard_opt_in" in data and data["leaderboard_opt_in"]:
        if not (data.get("leaderboard_alias") or profile.leaderboard_alias):
            raise ApiError(
                "validation_error",
                "leaderboard_alias is required when opting in.",
                422,
            )
    for field, value in data.items():
        setattr(profile, field, value)
    db.session.commit()
    return profile.to_dict()


def organization_payload(user: User) -> dict:
    if user.account_type != "organization" or user.organization_id is None:
        raise ApiError("forbidden", "This account is not an organization account.", 403)
    org = db.session.get(Organization, user.organization_id)
    if org is None:
        raise ApiError("not_found", "Organization not found.", 404)
    return org.to_dict()


def update_organization(user: User, payload) -> dict:
    if not user.is_org_owner or user.organization_id is None:
        raise ApiError("forbidden", "Only the organization owner can edit this profile.", 403)
    org = db.session.get(Organization, user.organization_id)
    if org is None:
        raise ApiError("not_found", "Organization not found.", 404)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "contact_email" and value is not None:
            value = str(value)
        setattr(org, field, value)
    db.session.commit()
    return org.to_dict()


def request_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    return (forwarded.split(",")[0].strip() or request.remote_addr or "unknown")[:80]
