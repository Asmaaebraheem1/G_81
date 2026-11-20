"""Dashboard, report aggregates, and CSV export."""

from __future__ import annotations

import csv
import io
from datetime import date

from flask import Response
from sqlalchemy import func

from app.core.errors import ApiError
from app.core.periods import month_starts, parse_iso_date, period_bounds, previous_period
from app.modules.catalog.models import EmissionCategory, EmissionFactor
from app.modules.records.models import ConsumptionRecord
from app.modules.records.queries import (
    category_totals,
    in_period,
    monthly_totals,
    owned_query,
    total_grams,
)
from app.modules.users.models import User


def _bounds(period: str, from_date: str | None = None, to_date: str | None = None):
    return period_bounds(period, from_date, to_date)


def _period_dict(start: date, end: date) -> dict:
    return {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "days": (end - start).days + 1,
        "label": f"{start.isoformat()} → {end.isoformat()}",
    }


def _goals_progress(user: User) -> list[dict]:
    from app.modules.goals.service import progress_for_user

    return progress_for_user(user)


def dashboard(user: User, period: str = "month", from_date=None, to_date=None) -> dict:
    start, end = _bounds(period, from_date, to_date)
    current_query = in_period(owned_query(user), start, end)
    grams = total_grams(current_query)
    record_count = current_query.count()
    days = max(1, (end - start).days + 1)
    prev_start, prev_end = previous_period(start, end)
    prev_grams = total_grams(in_period(owned_query(user), prev_start, prev_end))
    change = grams - prev_grams
    categories = category_totals(user, start, end)
    recent = (
        current_query.order_by(ConsumptionRecord.activity_date.desc(), ConsumptionRecord.id.desc())
        .limit(5)
        .all()
    )
    return {
        "period": _period_dict(start, end),
        "totals": {
            "emissions_grams": grams,
            "emissions_kg": round(grams / 1000, 2),
            "records": record_count,
            "avg_kg_per_day": round(grams / 1000 / days, 2),
        },
        "previous": {
            "from": prev_start.isoformat(),
            "to": prev_end.isoformat(),
            "emissions_grams": prev_grams,
            "emissions_kg": round(prev_grams / 1000, 2),
        },
        "change": {
            "emissions_grams": change,
            "emissions_kg": round(change / 1000, 2),
            "percent": round((change / prev_grams * 100) if prev_grams else 0, 1),
            "direction": "up" if change > 0 else ("down" if change < 0 else "flat"),
        },
        "categories": categories,
        "top_category": categories[0] if categories else None,
        "goals": _goals_progress(user),
        "recent_records": [record.to_dict() for record in recent],
    }


def report_summary(user: User, period: str = "month", from_date=None, to_date=None) -> dict:
    return dashboard(user, period, from_date, to_date)


def trend(user: User, months: int = 6) -> dict:
    starts = month_starts(months)
    data = monthly_totals(user, starts)
    totals = [row["emissions_grams"] for row in data]
    return {
        "months": months,
        "points": data,
        "total_grams": sum(totals),
        "total_kg": round(sum(totals) / 1000, 2),
    }


def categories(user: User, period: str = "month", from_date=None, to_date=None) -> dict:
    start, end = _bounds(period, from_date, to_date)
    rows = category_totals(user, start, end)
    total = sum(row["emissions_grams"] for row in rows)
    return {
        "period": _period_dict(start, end),
        "total_grams": total,
        "total_kg": round(total / 1000, 2),
        "categories": rows,
    }


def top_activities(
    user: User,
    period: str = "month",
    from_date=None,
    to_date=None,
    limit: int = 5,
) -> dict:
    start, end = _bounds(period, from_date, to_date)
    rows = (
        in_period(owned_query(user), start, end)
        .join(EmissionFactor, ConsumptionRecord.factor_id == EmissionFactor.id)
        .join(EmissionCategory, ConsumptionRecord.category_id == EmissionCategory.id)
        .with_entities(
            EmissionFactor.id,
            EmissionFactor.name_en,
            EmissionFactor.name_ar,
            EmissionCategory.name_en.label("category_en"),
            EmissionCategory.name_ar.label("category_ar"),
            EmissionFactor.unit,
            func.sum(ConsumptionRecord.emissions_grams).label("grams"),
            func.count(ConsumptionRecord.id).label("records"),
        )
        .group_by(EmissionFactor.id)
        .order_by(func.sum(ConsumptionRecord.emissions_grams).desc())
        .limit(limit)
        .all()
    )
    data = [
        {
            "factor_id": row.id,
            "name_en": row.name_en,
            "name_ar": row.name_ar,
            "category_en": row.category_en,
            "category_ar": row.category_ar,
            "unit": row.unit,
            "emissions_grams": int(row.grams or 0),
            "emissions_kg": round(int(row.grams or 0) / 1000, 2),
            "records": int(row.records or 0),
        }
        for row in rows
    ]
    return {"period": _period_dict(start, end), "activities": data}


def comparison(user: User, period: str = "month", from_date=None, to_date=None) -> dict:
    start, end = _bounds(period, from_date, to_date)
    prev_start, prev_end = previous_period(start, end)
    current_total = total_grams(in_period(owned_query(user), start, end))
    previous_total = total_grams(in_period(owned_query(user), prev_start, prev_end))
    current_categories = {row["category_id"]: row for row in category_totals(user, start, end)}
    previous_categories = {
        row["category_id"]: row for row in category_totals(user, prev_start, prev_end)
    }
    breakdown = []
    for category_id in sorted(set(current_categories) | set(previous_categories)):
        current = current_categories.get(category_id, {})
        previous = previous_categories.get(category_id, {})
        current_grams = int(current.get("emissions_grams", 0))
        previous_grams = int(previous.get("emissions_grams", 0))
        delta = current_grams - previous_grams
        breakdown.append(
            {
                "category_id": category_id,
                "name_en": current.get("name_en") or previous.get("name_en"),
                "name_ar": current.get("name_ar") or previous.get("name_ar"),
                "current_grams": current_grams,
                "previous_grams": previous_grams,
                "change_grams": delta,
                "change_percent": round((delta / previous_grams * 100) if previous_grams else 0, 1),
            }
        )
    delta = current_total - previous_total
    return {
        "current": _period_dict(start, end),
        "previous": _period_dict(prev_start, prev_end),
        "current_grams": current_total,
        "previous_grams": previous_total,
        "change_grams": delta,
        "change_percent": round((delta / previous_total * 100) if previous_total else 0, 1),
        "categories": breakdown,
    }


def export_csv(user: User, from_date: str, to_date: str) -> Response:
    start = parse_iso_date(from_date, "from")
    end = parse_iso_date(to_date, "to")
    if start is None or end is None:
        raise ApiError("validation_error", "from and to are required.", 422)
    if start > end:
        raise ApiError("validation_error", "from must be before to.", 422)
    records = (
        in_period(owned_query(user), start, end)
        .order_by(ConsumptionRecord.activity_date, ConsumptionRecord.id)
        .all()
    )
    buffer = io.StringIO()
    buffer.write("\ufeff")
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "record_id",
            "activity_date",
            "category",
            "factor",
            "quantity",
            "unit",
            "factor_grams_co2e",
            "factor_source",
            "emissions_grams",
            "emissions_kg",
            "notes",
            "formula",
        ]
    )
    for record in records:
        writer.writerow(
            [
                record.id,
                record.activity_date.isoformat(),
                record.category.name_en if record.category else "",
                record.factor.name_en if record.factor else "",
                f"{float(record.quantity):.4f}",
                record.unit,
                record.factor_grams_co2e_snapshot,
                record.factor_source_snapshot,
                record.emissions_grams,
                f"{record.emissions_kg:.2f}",
                record.notes or "",
                record.formula,
            ]
        )
    filename = f"carbonwise-records-{start.isoformat()}-{end.isoformat()}.csv"
    return Response(
        buffer.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
