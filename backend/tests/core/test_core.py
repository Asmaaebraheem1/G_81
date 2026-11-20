"""Unit tests for calculation, period, validator, text, and limiter helpers."""

from __future__ import annotations

from datetime import date

import pytest

from app.core.emissions import calculate_emissions_grams, factor_source_text
from app.core.errors import ApiError
from app.core.periods import (
    demo_today,
    month_starts,
    parse_iso_date,
    period_bounds,
    previous_period,
)
from app.core.rate_limit import RateLimiter
from app.core.text import excerpt, redact_pii, slugify, unique_slug
from app.core.validators import (
    clean_account_type,
    clean_email,
    clean_locale,
    clean_password,
    clean_timezone,
)


def test_calculate_emissions_rounds_half_up():
    assert calculate_emissions_grams(100, 233) == 23300
    assert calculate_emissions_grams("0.5", 3) == 2
    assert calculate_emissions_grams(1.2345, 100) == 123
    with pytest.raises(ApiError) as exc:
        calculate_emissions_grams(0, 10)
    assert exc.value.status == 422
    with pytest.raises(ApiError):
        calculate_emissions_grams(-1, 10)
    with pytest.raises(ApiError):
        calculate_emissions_grams("not-a-number", 10)
    with pytest.raises(ApiError):
        calculate_emissions_grams(1, -1)


def test_factor_source_text():
    class Factor:
        source_name = "DEFRA"
        source_year = 2025
        region = "UK"

    assert factor_source_text(Factor()) == "DEFRA (2025), UK"

    class NoYear(Factor):
        source_year = None

    assert factor_source_text(NoYear()) == "DEFRA (n.d.), UK"


def test_parse_iso_date():
    assert parse_iso_date("2026-06-30") == date(2026, 6, 30)
    assert parse_iso_date(None) is None
    assert parse_iso_date("") is None
    with pytest.raises(ApiError):
        parse_iso_date("30/06/2026")


def test_period_bounds(app):
    today = date(2026, 6, 30)  # Tuesday
    assert period_bounds("week", today=today) == (date(2026, 6, 29), date(2026, 7, 5))
    assert period_bounds("month", today=today) == (date(2026, 6, 1), date(2026, 6, 30))
    assert period_bounds("year", today=today) == (date(2026, 1, 1), date(2026, 12, 31))
    assert period_bounds("last_7_days", today=today) == (date(2026, 6, 24), today)
    assert period_bounds("last_30_days", today=today)[1] == today
    assert period_bounds("all", today=today) == (date(2025, 1, 1), today)
    assert period_bounds("month", "2026-01-01", "2026-02-01") == (
        date(2026, 1, 1),
        date(2026, 2, 1),
    )
    with pytest.raises(ApiError):
        period_bounds("month", "2026-02-01", "2026-01-01")
    with pytest.raises(ApiError):
        period_bounds("bogus")
    with pytest.raises(ApiError):
        period_bounds("month", "2026-01-01", None)


def test_previous_period_and_month_starts(app):
    assert previous_period(date(2026, 6, 1), date(2026, 6, 30)) == (
        date(2026, 5, 2),
        date(2026, 5, 31),
    )
    assert month_starts(3, date(2026, 6, 30)) == [
        date(2026, 4, 1),
        date(2026, 5, 1),
        date(2026, 6, 1),
    ]
    assert len(month_starts(99, date(2026, 6, 30))) == 24


def test_demo_today(app):
    assert demo_today() == date(2026, 6, 30)


def test_validators():
    assert clean_email(" Test@Example.COM ") == "test@example.com"
    with pytest.raises(ApiError):
        clean_email("bad")
    assert clean_password("Secret123") == "Secret123"
    with pytest.raises(ApiError):
        clean_password("short")
    with pytest.raises(ApiError):
        clean_password("onlyletters")
    assert clean_locale(None) == "ar"
    assert clean_locale("EN") == "en"
    with pytest.raises(ApiError):
        clean_locale("fr")
    assert clean_timezone("Africa/Cairo") == "Africa/Cairo"
    with pytest.raises(ApiError):
        clean_timezone("Not/AZone")
    assert clean_account_type("HOUSEHOLD") == "household"
    with pytest.raises(ApiError):
        clean_account_type("company")


def test_text_helpers():
    assert slugify("Hello, World!") == "hello-world"
    assert slugify("!!!") == "item"
    assert slugify("مرحبا") == "item"
    assert excerpt("one two three", 9) == "one two…"
    assert excerpt("short", 20) == "short"
    redacted = redact_pii("mail a@b.com card 4111 1111 1111 1111 phone +201234567890")
    assert "a@b.com" not in redacted
    assert "4111" not in redacted
    assert "[email]" in redacted


def test_unique_slug_appends_suffix(app, data):
    # The demo organization already owns green-demo-org.
    from app.modules.organizations.models import Organization

    assert unique_slug(Organization, "Green Demo Org") == "green-demo-org-2"


def test_rate_limiter():
    limiter = RateLimiter(limit=2, window_seconds=60)
    limiter.check("key")
    limiter.check("key")
    with pytest.raises(ApiError) as exc:
        limiter.check("key")
    assert exc.value.status == 429
    limiter.reset("key")
    limiter.check("key")
    limiter.reset()
    limiter.check("key")
