"""Challenge, achievement, and leaderboard endpoints."""

from __future__ import annotations

from flask import request
from flask_jwt_extended import jwt_required

from app.api.v1.blueprint import TAG_CHALLENGES, api_v1
from app.api.v1.deps import current_user
from app.api.v1.schemas import ChallengeProgressBody, IdPath
from app.core.errors import success
from app.modules.challenges import service


@api_v1.get("/challenges", tags=[TAG_CHALLENGES], summary="Active, upcoming, completed")
@jwt_required()
def list_challenges():
    return success(service.list_challenges(current_user(), request.args.get("status")))


@api_v1.get("/challenges/<int:id>", tags=[TAG_CHALLENGES], summary="Challenge detail")
@jwt_required()
def challenge_detail(path: IdPath):
    return success(service.get_challenge(current_user(), path.id))


@api_v1.post("/challenges/<int:id>/join", tags=[TAG_CHALLENGES], summary="Join a challenge")
@jwt_required()
def challenge_join(path: IdPath):
    return success(service.join(current_user(), path.id), 201)


@api_v1.get(
    "/challenges/<int:id>/progress",
    tags=[TAG_CHALLENGES],
    summary="Challenge progress + verification",
)
@jwt_required()
def challenge_progress(path: IdPath):
    return success(service.progress(current_user(), path.id))


@api_v1.post(
    "/challenges/<int:id>/progress",
    tags=[TAG_CHALLENGES],
    summary="Self-report or verify progress",
)
@jwt_required()
def challenge_report(path: IdPath, body: ChallengeProgressBody):
    return success(service.report_progress(current_user(), path.id, body))


@api_v1.get("/achievements", tags=[TAG_CHALLENGES], summary="Badges, points, milestones")
@jwt_required()
def achievements():
    return success(service.achievements(current_user()))


@api_v1.get("/leaderboard", tags=[TAG_CHALLENGES], summary="Opt-in leaderboard")
@jwt_required()
def leaderboard():
    period = request.args.get("period", "month")
    if period not in {"week", "month", "year"}:
        period = "month"
    return success(service.leaderboard(current_user(), period))
