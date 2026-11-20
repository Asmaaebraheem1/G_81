"""Goal service: baseline snapshots and progress."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import or_

from app.core.db import db
from app.core.errors import ApiError
from app.core.periods import demo_today
from app.modules.goals.models import Goal
from app.modules.records.queries import in_period, owned_query, total_grams
from app.modules.users.models import User


def _query(user: User):
    if user.organization_id:
        return Goal.query.filter(
            or_(
                Goal.user_id == user.id,
                Goal.organization_id == user.organization_id,
            )
        )
    return Goal.query.filter(Goal.user_id == user.id)


def list_goals(user: User, status: str | None = None) -> list[dict]:
    query = _query(user)
    if status:
        query = query.filter(Goal.status == status)
    goals = query.order_by(Goal.created_at.desc()).all()
    return [_with_progress(user, goal) for goal in goals]


def get_goal(user: User, goal_id: int) -> Goal:
    goal = _query(user).filter(Goal.id == goal_id).first()
    if goal is None:
        raise ApiError("not_found", "Goal not found.", 404)
    return goal


def create_goal(user: User, payload) -> dict:
    if payload.start_date > payload.end_date:
        raise ApiError("validation_error", "start_date must be before end_date.", 422)
    if payload.target_percent <= 0 or payload.target_percent > 100:
        raise ApiError("validation_error", "target_percent must be between 1 and 100.", 422)
    length = (payload.end_date - payload.start_date).days + 1
    if payload.baseline_start and payload.baseline_end:
        baseline_start, baseline_end = payload.baseline_start, payload.baseline_end
        if baseline_start > baseline_end:
            raise ApiError("validation_error", "baseline dates are invalid.", 422)
    else:
        baseline_end = payload.start_date - timedelta(days=1)
        baseline_start = baseline_end - timedelta(days=length - 1)
    baseline = total_grams(in_period(owned_query(user), baseline_start, baseline_end))
    if baseline <= 0:
        raise ApiError(
            "validation_error",
            "No emissions were found in the baseline period. Add records first.",
            422,
        )
    target = round(baseline * (1 - payload.target_percent / 100))
    goal = Goal(
        user_id=user.id,
        organization_id=user.organization_id if user.account_type == "organization" else None,
        title=payload.title.strip(),
        target_percent=payload.target_percent,
        period_type=payload.period_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
        baseline_emissions_grams=baseline,
        target_emissions_grams=target,
        status="active",
    )
    db.session.add(goal)
    db.session.commit()
    return _with_progress(user, goal)


def update_goal(user: User, goal_id: int, payload) -> dict:
    goal = get_goal(user, goal_id)
    data = payload.model_dump(exclude_unset=True)
    if "start_date" in data or "end_date" in data:
        start = data.get("start_date", goal.start_date)
        end = data.get("end_date", goal.end_date)
        if start > end:
            raise ApiError("validation_error", "start_date must be before end_date.", 422)
    for field, value in data.items():
        setattr(goal, field, value)
    db.session.commit()
    return _with_progress(user, goal)


def cancel_goal(user: User, goal_id: int) -> dict:
    goal = get_goal(user, goal_id)
    goal.status = "cancelled"
    db.session.commit()
    return {"cancelled": True, "id": goal.id}


def progress(user: User, goal_id: int) -> dict:
    return _with_progress(user, get_goal(user, goal_id))


def progress_for_user(user: User) -> list[dict]:
    goals = _query(user).filter(Goal.status == "active").order_by(Goal.end_date).all()
    return [_with_progress(user, goal) for goal in goals]


def _with_progress(user: User, goal: Goal) -> dict:
    today = demo_today()
    current_end = min(goal.end_date, today)
    if current_end < goal.start_date:
        current_grams = 0
    else:
        current_grams = total_grams(in_period(owned_query(user), goal.start_date, current_end))
    reduction = goal.baseline_emissions_grams - current_grams
    target_reduction = goal.baseline_emissions_grams - goal.target_emissions_grams
    achieved = round(reduction / target_reduction * 100, 1) if target_reduction > 0 else 0.0
    achieved = max(0.0, min(achieved, 100.0))
    days_left = (goal.end_date - today).days
    status = goal.status
    if status == "active":
        if goal.end_date < today:
            status = "completed" if current_grams <= goal.target_emissions_grams else "missed"
            goal.status = status
            db.session.commit()
        elif current_grams <= goal.target_emissions_grams and goal.end_date <= today:
            status = "completed"
    data = goal.to_dict()
    data.update(
        {
            "current_emissions_grams": current_grams,
            "current_emissions_kg": round(current_grams / 1000, 2),
            "baseline_emissions_kg": round(goal.baseline_emissions_grams / 1000, 2),
            "target_emissions_kg": round(goal.target_emissions_grams / 1000, 2),
            "reduction_grams": reduction,
            "reduction_kg": round(reduction / 1000, 2),
            "achieved_percent": achieved,
            "days_left": days_left,
            "status": status,
            "on_track": current_grams <= goal.target_emissions_grams,
        }
    )
    return data
