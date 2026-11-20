"""Reduction plan endpoints."""

from __future__ import annotations

from flask import request
from flask_jwt_extended import jwt_required

from app.api.v1.blueprint import TAG_PLANS, api_v1
from app.api.v1.deps import current_user
from app.api.v1.schemas import (
    IdPath,
    PlanActionPath,
    PlanActionUpdate,
    PlanGenerate,
    PlanUpdate,
)
from app.core.errors import success
from app.modules.plans import service


@api_v1.get("/plans", tags=[TAG_PLANS], summary="List plans")
@jwt_required()
def list_plans():
    return success(service.list_plans(current_user(), request.args.get("status")))


@api_v1.post("/plans/generate", tags=[TAG_PLANS], summary="Generate an AI/template plan")
@jwt_required()
def generate_plan(body: PlanGenerate):
    return success(service.generate(current_user(), body), 201)


@api_v1.get("/plans/<int:id>", tags=[TAG_PLANS], summary="Plan + actions")
@jwt_required()
def get_plan(path: IdPath):
    return success(service.get_plan(current_user(), path.id).to_dict())


@api_v1.patch("/plans/<int:id>", tags=[TAG_PLANS], summary="Edit plan status/title")
@jwt_required()
def update_plan(path: IdPath, body: PlanUpdate):
    return success(service.update_plan(current_user(), path.id, body))


@api_v1.patch(
    "/plans/<int:id>/actions/<int:action_id>",
    tags=[TAG_PLANS],
    summary="Update action status",
)
@jwt_required()
def update_action(path: PlanActionPath, body: PlanActionUpdate):
    return success(service.update_action(current_user(), path.id, path.action_id, body))


@api_v1.get("/plans/<int:id>/progress", tags=[TAG_PLANS], summary="Plan progress")
@jwt_required()
def plan_progress(path: IdPath):
    return success(service.progress(current_user(), path.id))
