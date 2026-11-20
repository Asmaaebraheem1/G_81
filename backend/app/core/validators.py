"""Small input validators shared by API and admin."""

from __future__ import annotations

import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.errors import ApiError

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_MIN = 8
VALID_LOCALES = {"en", "ar"}


def clean_email(value: str) -> str:
    email = (value or "").strip().lower()
    if not EMAIL_RE.match(email) or len(email) > 255:
        raise ApiError("validation_error", "A valid email is required.", 422)
    return email


def clean_password(value: str) -> str:
    password = value or ""
    if len(password) < PASSWORD_MIN:
        raise ApiError(
            "validation_error",
            f"Password must be at least {PASSWORD_MIN} characters.",
            422,
        )
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise ApiError(
            "validation_error",
            "Password must contain at least one letter and one number.",
            422,
        )
    return password


def clean_locale(value: str | None, default: str = "ar") -> str:
    locale = (value or default).strip().lower()
    if locale not in VALID_LOCALES:
        raise ApiError("validation_error", "locale must be en or ar", 422)
    return locale


def clean_timezone(value: str | None, default: str = "UTC") -> str:
    tz = (value or default).strip()
    try:
        ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ApiError("validation_error", "timezone must be a valid IANA name", 422) from exc
    return tz


def clean_account_type(value: str | None) -> str:
    account_type = (value or "individual").strip().lower()
    if account_type not in {"individual", "household", "organization"}:
        raise ApiError(
            "validation_error",
            "account_type must be individual, household, or organization",
            422,
        )
    return account_type
