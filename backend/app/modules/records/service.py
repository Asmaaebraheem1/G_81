"""Consumption record CRUD and transparent calculations."""

from __future__ import annotations

from datetime import date

from sqlalchemy import or_

from app.core.db import db, utcnow
from app.core.emissions import (
    calculate_emissions_grams,
    factor_source_text,
    validate_factor_for_record,
)
from app.core.errors import ApiError
from app.core.periods import demo_today, parse_iso_date
from app.core.responses import paginated
from app.modules.catalog.models import EmissionCategory, EmissionFactor
from app.modules.records.models import ConsumptionRecord
from app.modules.records.queries import owned_query
from app.modules.users.models import User


def _get_category(category_id: int) -> EmissionCategory:
    category = db.session.get(EmissionCategory, category_id)
    if category is None or not category.is_active:
        raise ApiError("validation_error", "Category not found or inactive.", 422)
    return category


def _get_factor(factor_id: int) -> EmissionFactor:
    factor = db.session.get(EmissionFactor, factor_id)
    if factor is None:
        raise ApiError("validation_error", "Emission factor not found.", 422)
    return factor


def _validate_date(value: date) -> date:
    if value > demo_today():
        raise ApiError("validation_error", "activity_date cannot be in the future.", 422)
    return value


def list_records(user: User, query) -> dict:
    db_query = owned_query(user)
    start = parse_iso_date(query.from_date, "from")
    end = parse_iso_date(query.to_date, "to")
    if bool(start) ^ bool(end):
        raise ApiError("validation_error", "from and to must be provided together.", 422)
    if start and end:
        if start > end:
            raise ApiError("validation_error", "from must be before to.", 422)
        db_query = db_query.filter(ConsumptionRecord.activity_date.between(start, end))
    if query.category_id:
        db_query = db_query.filter(ConsumptionRecord.category_id == query.category_id)
    if query.q:
        like = f"%{query.q.strip()}%"
        db_query = db_query.join(EmissionCategory).filter(
            or_(
                ConsumptionRecord.notes.ilike(like),
                EmissionCategory.name_en.ilike(like),
                EmissionCategory.name_ar.ilike(like),
            )
        )
    sort_map = {
        "-activity_date": ConsumptionRecord.activity_date.desc(),
        "activity_date": ConsumptionRecord.activity_date.asc(),
        "-emissions_grams": ConsumptionRecord.emissions_grams.desc(),
        "emissions_grams": ConsumptionRecord.emissions_grams.asc(),
    }
    db_query = db_query.order_by(sort_map[query.sort], ConsumptionRecord.id.desc())
    page = db_query.paginate(page=query.page, per_page=query.per_page, error_out=False)
    return paginated(
        page.items,
        page.page,
        page.per_page,
        page.total,
        lambda record: record.to_dict(),
    )


def create_record(user: User, payload, source: str = "manual", document=None) -> dict:
    category = _get_category(payload.category_id)
    factor = _get_factor(payload.factor_id)
    validate_factor_for_record(factor, category.id, payload.unit)
    activity_date = _validate_date(payload.activity_date)
    grams = calculate_emissions_grams(payload.quantity, factor.factor_grams_co2e)
    record = ConsumptionRecord(
        user_id=user.id,
        organization_id=user.organization_id if user.account_type == "organization" else None,
        category_id=category.id,
        factor_id=factor.id,
        activity_date=activity_date,
        quantity=payload.quantity,
        unit=factor.unit,
        factor_grams_co2e_snapshot=factor.factor_grams_co2e,
        factor_source_snapshot=factor_source_text(factor),
        emissions_grams=grams,
        notes=getattr(payload, "notes", None),
        status="active",
        source=source,
    )
    db.session.add(record)
    db.session.flush()
    if document is not None:
        document.record_id = record.id
        document.status = "confirmed"
        document.confirmed_at = utcnow()
        record.document_id = document.id
    db.session.commit()
    _maybe_notify_increase(user)
    return record.to_dict()


def get_record(user: User, record_id: int) -> ConsumptionRecord:
    record = owned_query(user).filter(ConsumptionRecord.id == record_id).first()
    if record is None:
        raise ApiError("not_found", "Record not found.", 404)
    return record


def update_record(user: User, record_id: int, payload) -> dict:
    record = get_record(user, record_id)
    data = payload.model_dump(exclude_unset=True)
    category_id = data.get("category_id", record.category_id)
    factor_id = data.get("factor_id", record.factor_id)
    unit = data.get("unit", record.unit)
    category = _get_category(category_id)
    factor = _get_factor(factor_id)
    validate_factor_for_record(factor, category.id, unit)
    if "activity_date" in data:
        _validate_date(data["activity_date"])
    recalc = any(key in data for key in ("quantity", "factor_id", "unit", "category_id"))
    for field in ("category_id", "factor_id", "activity_date", "quantity", "unit", "notes"):
        if field in data:
            setattr(record, field, data[field])
    if "unit" in data:
        record.unit = factor.unit
    if recalc:
        record.factor_grams_co2e_snapshot = factor.factor_grams_co2e
        record.factor_source_snapshot = factor_source_text(factor)
        record.emissions_grams = calculate_emissions_grams(
            record.quantity, factor.factor_grams_co2e
        )
    db.session.commit()
    return record.to_dict()


def delete_record(user: User, record_id: int) -> dict:
    record = get_record(user, record_id)
    record.status = "deleted"
    db.session.commit()
    return {"deleted": True, "id": record.id}


def calculation(user: User, record_id: int) -> dict:
    record = get_record(user, record_id)
    return {
        "record_id": record.id,
        "quantity": float(record.quantity),
        "unit": record.unit,
        "factor_grams_co2e": record.factor_grams_co2e_snapshot,
        "factor_source": record.factor_source_snapshot,
        "emissions_grams": record.emissions_grams,
        "emissions_kg": record.emissions_kg,
        "formula": record.formula,
        "note": (
            "Calculated by the backend with the factor snapshot stored on this record. "
            "Historical totals do not change when an admin edits a factor."
        ),
    }


def _maybe_notify_increase(user: User) -> None:
    """Create an in-app alert after a significant month-over-month increase."""
    try:
        from app.modules.notifications.service import maybe_notify_significant_increase

        maybe_notify_significant_increase(user)
    except Exception:  # noqa: BLE001
        db.session.rollback()
        # Notifications must never break record creation.
