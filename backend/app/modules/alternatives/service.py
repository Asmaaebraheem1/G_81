"""Saved alternatives and personalized recommendations."""

from __future__ import annotations

from app.core.db import db
from app.core.errors import ApiError
from app.modules.alternatives.models import Alternative, SavedAlternative
from app.modules.users.models import User


def get_alternative(alternative_id: int) -> Alternative:
    item = db.session.get(Alternative, alternative_id)
    if item is None or not item.is_active:
        raise ApiError("not_found", "Alternative not found.", 404)
    return item


def set_status(user: User, alternative_id: int, status: str) -> dict:
    alternative = get_alternative(alternative_id)
    row = SavedAlternative.query.filter_by(user_id=user.id, alternative_id=alternative.id).first()
    if row is None:
        row = SavedAlternative(
            user_id=user.id,
            alternative_id=alternative.id,
            status=status,
        )
        db.session.add(row)
    else:
        row.status = status
    db.session.commit()
    return {
        "id": row.id,
        "alternative_id": alternative.id,
        "status": row.status,
        "alternative": alternative.to_dict(),
    }


def list_saved(user: User) -> list[dict]:
    rows = (
        SavedAlternative.query.filter_by(user_id=user.id)
        .order_by(SavedAlternative.updated_at.desc())
        .all()
    )
    return [row.to_dict() for row in rows]


def recommended(user: User, locale: str = "en") -> dict:
    from app.modules.ai import service as ai_service

    result = ai_service.recommend_alternatives(user, locale)
    saved = {
        row.alternative_id: row.status
        for row in SavedAlternative.query.filter_by(user_id=user.id).all()
    }
    items = []
    for item in result["items"]:
        item = dict(item)
        item["saved_status"] = saved.get(item["id"])
        items.append(item)
    return {
        "source": result["source"],
        "rationale": result.get("rationale", ""),
        "alternatives": items,
        "note": (
            "Reduction percentages are curated catalog assumptions, not AI-generated "
            "emission values."
        ),
    }
