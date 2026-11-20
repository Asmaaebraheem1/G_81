"""Reusable consumption-record queries."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, or_

from app.modules.catalog.models import EmissionCategory
from app.modules.records.models import ConsumptionRecord
from app.modules.users.models import User


def owned_query(user: User, include_deleted: bool = False):
    query = ConsumptionRecord.query
    if user.organization_id:
        query = query.filter(
            or_(
                ConsumptionRecord.user_id == user.id,
                ConsumptionRecord.organization_id == user.organization_id,
            )
        )
    else:
        query = query.filter(ConsumptionRecord.user_id == user.id)
    if not include_deleted:
        query = query.filter(ConsumptionRecord.status == "active")
    return query


def in_period(query, start: date, end: date):
    return query.filter(ConsumptionRecord.activity_date.between(start, end))


def total_grams(query) -> int:
    value = query.with_entities(
        func.coalesce(func.sum(ConsumptionRecord.emissions_grams), 0)
    ).scalar()
    return int(value or 0)


def category_totals(user: User, start: date, end: date) -> list[dict]:
    rows = (
        in_period(owned_query(user), start, end)
        .join(EmissionCategory, ConsumptionRecord.category_id == EmissionCategory.id)
        .with_entities(
            EmissionCategory.id,
            EmissionCategory.key,
            EmissionCategory.name_en,
            EmissionCategory.name_ar,
            EmissionCategory.color_hex,
            EmissionCategory.icon,
            func.sum(ConsumptionRecord.emissions_grams).label("grams"),
            func.count(ConsumptionRecord.id).label("records"),
        )
        .group_by(EmissionCategory.id)
        .order_by(func.sum(ConsumptionRecord.emissions_grams).desc())
        .all()
    )
    total = sum(int(row.grams or 0) for row in rows)
    result = []
    for row in rows:
        grams = int(row.grams or 0)
        result.append(
            {
                "category_id": row.id,
                "key": row.key,
                "name_en": row.name_en,
                "name_ar": row.name_ar,
                "color_hex": row.color_hex,
                "icon": row.icon,
                "emissions_grams": grams,
                "emissions_kg": round(grams / 1000, 2),
                "share_percent": round((grams / total * 100) if total else 0, 1),
                "records": int(row.records or 0),
            }
        )
    return result


def monthly_totals(user: User, starts: list[date]) -> list[dict]:
    result = []
    for start in starts:
        if start.month == 12:
            end = date(start.year + 1, 1, 1)
        else:
            end = date(start.year, start.month + 1, 1)
        grams = total_grams(in_period(owned_query(user), start, end))
        result.append(
            {
                "month": start.strftime("%Y-%m"),
                "label": start.strftime("%b %Y"),
                "emissions_grams": grams,
                "emissions_kg": round(grams / 1000, 2),
            }
        )
    return result
