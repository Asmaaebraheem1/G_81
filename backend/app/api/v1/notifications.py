"""Notification endpoints."""

from __future__ import annotations

from flask import request
from flask_jwt_extended import jwt_required

from app.api.v1.blueprint import TAG_NOTIFICATIONS, api_v1
from app.api.v1.deps import current_user
from app.api.v1.schemas import IdPath, PreferencesUpdate
from app.core.errors import success
from app.modules.notifications import service


@api_v1.get("/notifications", tags=[TAG_NOTIFICATIONS], summary="List notifications")
@jwt_required()
def list_notifications():
    unread = request.args.get("unread") in {"1", "true", "yes"}
    return success(
        {
            "notifications": service.list_notifications(current_user(), unread),
            "unread_count": service.unread_count(current_user()),
        }
    )


@api_v1.patch("/notifications/<int:id>/read", tags=[TAG_NOTIFICATIONS], summary="Mark one read")
@jwt_required()
def mark_read(path: IdPath):
    return success(service.mark_read(current_user(), path.id))


@api_v1.post("/notifications/read-all", tags=[TAG_NOTIFICATIONS], summary="Mark all read")
@jwt_required()
def mark_all_read():
    return success(service.mark_all_read(current_user()))


@api_v1.get(
    "/notification-preferences",
    tags=[TAG_NOTIFICATIONS],
    summary="Notification preferences",
)
@jwt_required()
def get_preferences():
    return success(service.get_preferences(current_user()))


@api_v1.patch(
    "/notification-preferences",
    tags=[TAG_NOTIFICATIONS],
    summary="Update notification preferences",
)
@jwt_required()
def update_preferences(body: PreferencesUpdate):
    return success(service.update_preferences(current_user(), body))
