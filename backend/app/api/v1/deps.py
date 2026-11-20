"""Shared API dependencies and query helpers."""

from __future__ import annotations

from flask_jwt_extended import get_jwt, get_jwt_identity
from sqlalchemy import or_

from app.core.db import db
from app.core.errors import ApiError
from app.modules.users.models import User


def current_user() -> User:
    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError) as exc:
        raise ApiError("invalid_token", "The token identity is invalid.", 401) from exc
    user = db.session.get(User, user_id)
    if user is None:
        raise ApiError("unauthorized", "Account not found.", 401)
    if not user.is_active:
        raise ApiError("account_inactive", "This account is suspended.", 403)
    return user


def require_org_owner(user: User) -> None:
    if not user.is_org_owner or user.organization_id is None:
        raise ApiError("forbidden", "Only the organization owner can do this.", 403)


def record_scope(user: User):
    """Rows a user may see: own rows, plus org rows for org accounts."""
    from app.modules.records.models import ConsumptionRecord

    if user.organization_id:
        return or_(
            ConsumptionRecord.user_id == user.id,
            ConsumptionRecord.organization_id == user.organization_id,
        )
    return ConsumptionRecord.user_id == user.id


def jwt_type() -> str:
    return str(get_jwt().get("type", "access"))
