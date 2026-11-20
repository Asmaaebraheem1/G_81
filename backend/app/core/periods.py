"""Period calculations for reports, goals, and the demo clock."""

from __future__ import annotations

from datetime import date, timedelta

from flask import current_app

from app.core.errors import ApiError

VALID_PERIODS = {"week", "month", "year", "last_7_days", "last_30_days", "all"}


def demo_today() -> date:
    """The deterministic 'today' for the local demo.

    The seeded timeline ends on DEMO_TODAY; using it for period defaults keeps
    the demo coherent no matter when it is opened. In a production deployment
    this would be the real UTC date.
    """
    value = current_app.config.get("DEMO_TODAY")
    if isinstance(value, date):
        return value
    return date.today()


def parse_iso_date(value: str | None, field: str = "date") -> date | None:
    if value is None or value == "":
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ApiError("validation_error", f"{field} must be YYYY-MM-DD", 422) from exc


def period_bounds(
    period: str = "month",
    start: str | date | None = None,
    end: str | date | None = None,
    today: date | None = None,
) -> tuple[date, date]:
    """Return inclusive start/end dates for a named or explicit period."""
    if period not in VALID_PERIODS:
        raise ApiError(
            "validation_error",
            "period must be week, month, year, last_7_days, last_30_days, or all",
            422,
        )
    if isinstance(start, str):
        start = parse_iso_date(start, "from")
    if isinstance(end, str):
        end = parse_iso_date(end, "to")
    if start or end:
        if not start or not end:
            raise ApiError("validation_error", "from and to must be provided together", 422)
        if start > end:
            raise ApiError("validation_error", "from must be before to", 422)
        return start, end

    today = today or demo_today()
    if period == "week":
        start_date = today - timedelta(days=today.weekday())
        return start_date, start_date + timedelta(days=6)
    if period == "month":
        start_date = today.replace(day=1)
        if today.month == 12:
            next_month = date(today.year + 1, 1, 1)
        else:
            next_month = date(today.year, today.month + 1, 1)
        return start_date, next_month - timedelta(days=1)
    if period == "year":
        return date(today.year, 1, 1), date(today.year, 12, 31)
    if period == "last_7_days":
        return today - timedelta(days=6), today
    if period == "last_30_days":
        return today - timedelta(days=29), today
    # "all" is bounded by the deterministic seed window in the local demo.
    seed = current_app.config.get("DEMO_SEED_DATE", today)
    if isinstance(seed, str):
        seed = date.fromisoformat(seed)
    return date(seed.year - 1, 1, 1), seed


def previous_period(start: date, end: date) -> tuple[date, date]:
    length = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    return prev_end - timedelta(days=length - 1), prev_end


def month_starts(months: int, end: date | None = None) -> list[date]:
    """Return the first day of the last `months` months, oldest first."""
    end = end or demo_today()
    cursor = end.replace(day=1)
    result: list[date] = []
    for _ in range(max(1, min(months, 24))):
        result.append(cursor)
        if cursor.month == 1:
            cursor = date(cursor.year - 1, 12, 1)
        else:
            cursor = date(cursor.year, cursor.month - 1, 1)
    return list(reversed(result))
