"""In-app notifications, preferences, and significant-increase alerts."""

from __future__ import annotations

from datetime import datetime, time

from app.core.db import db, utcnow
from app.core.errors import ApiError
from app.core.periods import period_bounds, previous_period
from app.modules.notifications.models import Notification, NotificationPreference
from app.modules.records.queries import in_period, owned_query, total_grams
from app.modules.users.models import User

DEFAULT_TYPES = [
    "reminder",
    "goal",
    "alert",
    "plan",
    "challenge",
    "summary",
    "announcement",
]


def create_notification(
    user_id: int | None,
    type: str,
    title_en: str,
    title_ar: str,
    body_en: str,
    body_ar: str,
    action_url: str | None = None,
) -> list[Notification]:
    if user_id is None:
        users = User.query.filter_by(is_active=True).all()
        rows = [
            Notification(
                user_id=user.id,
                type=type,
                title_en=title_en,
                title_ar=title_ar,
                body_en=body_en,
                body_ar=body_ar,
                action_url=action_url,
                is_read=False,
                created_at=utcnow(),
            )
            for user in users
        ]
    else:
        rows = [
            Notification(
                user_id=user_id,
                type=type,
                title_en=title_en,
                title_ar=title_ar,
                body_en=body_en,
                body_ar=body_ar,
                action_url=action_url,
                is_read=False,
                created_at=utcnow(),
            )
        ]
    db.session.add_all(rows)
    db.session.commit()
    return rows


def list_notifications(user: User, unread_only: bool = False) -> list[dict]:
    query = Notification.query.filter_by(user_id=user.id)
    if unread_only:
        query = query.filter_by(is_read=False)
    rows = query.order_by(Notification.created_at.desc()).limit(100).all()
    return [row.to_dict() for row in rows]


def unread_count(user: User) -> int:
    return Notification.query.filter_by(user_id=user.id, is_read=False).count()


def mark_read(user: User, notification_id: int) -> dict:
    row = Notification.query.filter_by(id=notification_id, user_id=user.id).first()
    if row is None:
        raise ApiError("not_found", "Notification not found.", 404)
    row.is_read = True
    row.read_at = utcnow()
    db.session.commit()
    return row.to_dict()


def mark_all_read(user: User) -> dict:
    count = Notification.query.filter_by(user_id=user.id, is_read=False).update(
        {"is_read": True, "read_at": utcnow()}
    )
    db.session.commit()
    return {"updated": count}


def get_preferences(user: User) -> list[dict]:
    rows = {row.type: row for row in NotificationPreference.query.filter_by(user_id=user.id).all()}
    return [
        {
            "type": type_name,
            "enabled": rows[type_name].enabled if type_name in rows else True,
        }
        for type_name in DEFAULT_TYPES
    ]


def update_preferences(user: User, payload) -> list[dict]:
    existing = {
        row.type: row for row in NotificationPreference.query.filter_by(user_id=user.id).all()
    }
    for item in payload.preferences:
        row = existing.get(item.type)
        if row is None:
            row = NotificationPreference(user_id=user.id, type=item.type, enabled=item.enabled)
            db.session.add(row)
        else:
            row.enabled = item.enabled
    db.session.commit()
    return get_preferences(user)


def maybe_notify_significant_increase(user: User) -> None:
    """Create at most one alert per demo month when emissions jump."""
    start, end = period_bounds("month")
    prev_start, prev_end = previous_period(start, end)
    current = total_grams(in_period(owned_query(user), start, end))
    previous = total_grams(in_period(owned_query(user), prev_start, prev_end))
    if previous <= 0 or current <= 0:
        return
    change = (current - previous) / previous * 100
    from flask import current_app

    threshold = float(current_app.config.get("SIGNIFICANT_INCREASE_PERCENT", 20))
    minimum = float(current_app.config.get("SIGNIFICANT_INCREASE_MIN_KG", 10))
    if change < threshold or (current - previous) / 1000 < minimum:
        return
    month_start = datetime.combine(start, time.min)
    exists = (
        Notification.query.filter_by(user_id=user.id, type="alert")
        .filter(Notification.created_at >= month_start)
        .first()
    )
    if exists:
        return
    create_notification(
        user.id,
        "alert",
        "Your emissions increased",
        "ارتفعت انبعاثاتك",
        f"Your calculated emissions are {change:.0f}% higher than the previous period. "
        "Open your report to see the largest category.",
        f"انبعاثاتك المحسوبة أعلى بنسبة {change:.0f}% من الفترة السابقة. "
        "افتح تقريرك لمعرفة الفئة الأكبر.",
        action_url="/reports",
    )
