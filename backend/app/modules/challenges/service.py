"""Challenges, progress verification, badges, points, and leaderboard."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func

from app.core.db import db, utcnow
from app.core.errors import ApiError
from app.core.periods import demo_today, period_bounds
from app.modules.challenges.models import (
    Badge,
    Challenge,
    ChallengeParticipant,
    PointsLedger,
    UserBadge,
)
from app.modules.records.queries import in_period, owned_query, total_grams
from app.modules.users.models import User, UserProfile


def _challenge_status(challenge: Challenge, today: date | None = None) -> str:
    today = today or demo_today()
    if challenge.start_date > today:
        return "upcoming"
    if challenge.end_date < today:
        return "completed"
    return "active"


def _participant(user: User, challenge_id: int) -> ChallengeParticipant | None:
    return ChallengeParticipant.query.filter_by(user_id=user.id, challenge_id=challenge_id).first()


def _payload(user: User, challenge: Challenge) -> dict:
    data = challenge.to_dict()
    data["challenge_status"] = _challenge_status(challenge)
    participant = _participant(user, challenge.id)
    data["participation"] = participant.to_dict() if participant else None
    return data


def list_challenges(user: User, status: str | None = None) -> list[dict]:
    query = Challenge.query.filter_by(is_active=True)
    rows = query.order_by(Challenge.start_date.desc()).all()
    data = [_payload(user, challenge) for challenge in rows]
    if status in {"active", "upcoming", "completed"}:
        data = [item for item in data if item["challenge_status"] == status]
    return data


def get_challenge(user: User, challenge_id: int) -> dict:
    challenge = db.session.get(Challenge, challenge_id)
    if challenge is None or not challenge.is_active:
        raise ApiError("not_found", "Challenge not found.", 404)
    data = _payload(user, challenge)
    data["progress"] = progress(user, challenge_id)
    return data


def join(user: User, challenge_id: int) -> dict:
    challenge = db.session.get(Challenge, challenge_id)
    if challenge is None or not challenge.is_active:
        raise ApiError("not_found", "Challenge not found.", 404)
    if challenge.end_date < demo_today():
        raise ApiError("conflict", "This challenge has already ended.", 409)
    participant = _participant(user, challenge_id)
    if participant is not None:
        return participant.to_dict()
    participant = ChallengeParticipant(
        challenge_id=challenge_id,
        user_id=user.id,
        progress_value=0,
        status="joined",
        joined_at=utcnow(),
    )
    db.session.add(participant)
    db.session.commit()
    return participant.to_dict()


def _computed_progress(user: User, challenge: Challenge) -> float:
    start = challenge.start_date
    end = min(challenge.end_date, demo_today())
    if end < start:
        return 0.0
    if challenge.target_type == "record_count":
        query = in_period(owned_query(user), start, end)
        if challenge.category_id:
            query = query.filter_by(category_id=challenge.category_id)
        return float(query.count())
    if challenge.target_type == "reduction_percent":
        current = total_grams(in_period(owned_query(user), start, end))
        length = (end - start).days + 1
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=length - 1)
        previous = total_grams(in_period(owned_query(user), prev_start, prev_end))
        if previous <= 0:
            return 0.0
        return max(0.0, round((previous - current) / previous * 100, 1))
    if challenge.target_type == "action_count":
        from app.modules.plans.models import PlanAction, ReductionPlan

        count = (
            PlanAction.query.join(ReductionPlan)
            .filter(
                ReductionPlan.user_id == user.id,
                PlanAction.status == "completed",
                PlanAction.completed_at.isnot(None),
            )
            .count()
        )
        return float(count)
    if challenge.target_type == "streak":
        return float(_longest_streak(user, start, end))
    return 0.0


def _longest_streak(user: User, start: date, end: date) -> int:
    from app.modules.records.models import ConsumptionRecord

    rows = (
        in_period(owned_query(user), start, end)
        .with_entities(ConsumptionRecord.activity_date)
        .distinct()
        .order_by(ConsumptionRecord.activity_date)
        .all()
    )
    dates = [row[0] for row in rows]
    best = 0
    current = 0
    previous = None
    for day in dates:
        if previous is not None and (day - previous).days == 1:
            current += 1
        else:
            current = 1
        best = max(best, current)
        previous = day
    return best


def _award(user: User, challenge: Challenge) -> None:
    participant = _participant(user, challenge.id)
    if participant is None or participant.status == "completed":
        return
    participant.status = "completed"
    participant.completed_at = utcnow()
    if challenge.points:
        db.session.add(
            PointsLedger(
                user_id=user.id,
                points=challenge.points,
                reason=f"Completed challenge: {challenge.title_en}",
                reference_type="challenge",
                reference_id=challenge.id,
                created_at=utcnow(),
            )
        )
    if challenge.badge_id:
        exists = UserBadge.query.filter_by(user_id=user.id, badge_id=challenge.badge_id).first()
        if exists is None:
            db.session.add(
                UserBadge(
                    user_id=user.id,
                    badge_id=challenge.badge_id,
                    awarded_at=utcnow(),
                )
            )
    db.session.commit()
    try:
        from app.modules.notifications.service import create_notification

        create_notification(
            user.id,
            "challenge",
            "Challenge completed",
            "اكتمل التحدي",
            f"You completed “{challenge.title_en}”.",
            f"أكملت “{challenge.title_ar}”.",
            action_url=f"/challenges/{challenge.id}",
        )
    except Exception:  # noqa: BLE001
        db.session.rollback()


def progress(user: User, challenge_id: int) -> dict:
    challenge = db.session.get(Challenge, challenge_id)
    if challenge is None:
        raise ApiError("not_found", "Challenge not found.", 404)
    participant = _participant(user, challenge.id)
    computed = _computed_progress(user, challenge)
    if participant is not None:
        participant.progress_value = max(float(participant.progress_value or 0), computed)
        if participant.progress_value < float(challenge.target_value):
            participant.status = "in_progress" if participant.progress_value > 0 else "joined"
        db.session.commit()
        if participant.progress_value >= float(challenge.target_value):
            _award(user, challenge)
            participant = _participant(user, challenge.id)
    target = float(challenge.target_value or 0)
    value = float(participant.progress_value) if participant else computed
    return {
        "challenge_id": challenge.id,
        "target_type": challenge.target_type,
        "target_value": target,
        "value": round(value, 2),
        "percent": round(min(100.0, (value / target * 100) if target else 0), 1),
        "status": participant.status if participant else "not_joined",
        "verified": challenge.target_type
        in {"record_count", "reduction_percent", "action_count", "streak"},
        "verification_note": (
            "Progress is calculated from your backend records."
            if challenge.target_type
            in {"record_count", "reduction_percent", "action_count", "streak"}
            else "Self-reported progress."
        ),
        "joined": participant is not None,
    }


def report_progress(user: User, challenge_id: int, payload) -> dict:
    challenge = db.session.get(Challenge, challenge_id)
    if challenge is None or not challenge.is_active:
        raise ApiError("not_found", "Challenge not found.", 404)
    participant = _participant(user, challenge_id)
    if participant is None:
        raise ApiError("conflict", "Join this challenge first.", 409)
    if payload.value is not None:
        participant.progress_value = max(float(participant.progress_value or 0), payload.value)
    else:
        participant.progress_value = max(
            float(participant.progress_value or 0), _computed_progress(user, challenge)
        )
    if participant.progress_value >= float(challenge.target_value):
        _award(user, challenge)
    else:
        participant.status = "in_progress"
        db.session.commit()
    return progress(user, challenge_id)


def achievements(user: User) -> dict:
    badges = UserBadge.query.filter_by(user_id=user.id).order_by(UserBadge.awarded_at.desc()).all()
    total_points = (
        db.session.query(func.coalesce(func.sum(PointsLedger.points), 0))
        .filter(PointsLedger.user_id == user.id)
        .scalar()
    )
    from app.modules.goals.models import Goal
    from app.modules.plans.models import ReductionPlan

    return {
        "points": int(total_points or 0),
        "badges": [
            {**row.badge.to_dict(), "awarded_at": row.awarded_at.isoformat() + "Z"}
            for row in badges
            if row.badge is not None
        ],
        "milestones": {
            "records": owned_query(user).count(),
            "goals_completed": Goal.query.filter_by(user_id=user.id, status="completed").count(),
            "plans_completed": ReductionPlan.query.filter_by(
                user_id=user.id, status="completed"
            ).count(),
            "challenges_completed": ChallengeParticipant.query.filter_by(
                user_id=user.id, status="completed"
            ).count(),
        },
        "all_badges": [badge.to_dict() for badge in Badge.query.order_by(Badge.id).all()],
    }


def leaderboard(user: User, period: str = "month") -> dict:
    from datetime import datetime
    from datetime import time as dt_time

    start, end = period_bounds(period)
    start_dt = datetime.combine(start, dt_time.min)
    end_dt = datetime.combine(end, dt_time.max)
    rows = (
        db.session.query(
            User.id,
            UserProfile.leaderboard_alias,
            User.full_name,
            func.coalesce(func.sum(PointsLedger.points), 0).label("points"),
        )
        .join(UserProfile, UserProfile.user_id == User.id)
        .outerjoin(PointsLedger, PointsLedger.user_id == User.id)
        .filter(UserProfile.leaderboard_opt_in.is_(True), User.is_active.is_(True))
        .filter((PointsLedger.id.is_(None)) | (PointsLedger.created_at.between(start_dt, end_dt)))
        .group_by(User.id)
        .order_by(func.coalesce(func.sum(PointsLedger.points), 0).desc())
        .limit(50)
        .all()
    )
    entries = []
    for index, row in enumerate(rows, start=1):
        entries.append(
            {
                "rank": index,
                "alias": row.leaderboard_alias or row.full_name,
                "points": int(row.points or 0),
                "is_me": row.id == user.id,
            }
        )
    return {
        "period": {"from": start.isoformat(), "to": end.isoformat()},
        "opt_in": bool(user.profile and user.profile.leaderboard_opt_in),
        "entries": entries,
        "note": "Only opted-in users appear. Aliases are shown instead of emails.",
    }
