"""Goal endpoints."""

from __future__ import annotations

from flask import request
from flask_jwt_extended import jwt_required

from app.api.v1.blueprint import TAG_GOALS, api_v1
from app.api.v1.deps import current_user
from app.api.v1.schemas import GoalCreate, GoalUpdate, IdPath
from app.core.errors import success
from app.modules.goals import service


@api_v1.get("/goals", tags=[TAG_GOALS], summary="List goals")
@jwt_required()
def list_goals():
    status = request.args.get("status")
    return success(service.list_goals(current_user(), status))


@api_v1.post("/goals", tags=[TAG_GOALS], summary="Create a goal with computed baseline")
@jwt_required()
def create_goal(body: GoalCreate):
    return success(service.create_goal(current_user(), body), 201)


@api_v1.get("/goals/<int:id>", tags=[TAG_GOALS], summary="Goal detail")
@jwt_required()
def get_goal(path: IdPath):
    return success(service.progress(current_user(), path.id))


@api_v1.patch("/goals/<int:id>", tags=[TAG_GOALS], summary="Edit a goal")
@jwt_required()
def update_goal(path: IdPath, body: GoalUpdate):
    return success(service.update_goal(current_user(), path.id, body))


@api_v1.delete("/goals/<int:id>", tags=[TAG_GOALS], summary="Cancel a goal")
@jwt_required()
def cancel_goal(path: IdPath):
    return success(service.cancel_goal(current_user(), path.id))


@api_v1.get("/goals/<int:id>/progress", tags=[TAG_GOALS], summary="Goal progress")
@jwt_required()
def goal_progress(path: IdPath):
    return success(service.progress(current_user(), path.id))
