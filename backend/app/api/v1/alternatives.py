"""Personalized alternatives endpoints."""

from __future__ import annotations

from flask import request
from flask_jwt_extended import jwt_required

from app.api.v1.blueprint import TAG_ALTERNATIVES, api_v1
from app.api.v1.deps import current_user
from app.api.v1.schemas import IdPath, SaveAlternativeBody
from app.core.errors import success
from app.modules.alternatives import service


@api_v1.get(
    "/alternatives/recommended",
    tags=[TAG_ALTERNATIVES],
    summary="Personalized alternatives",
)
@jwt_required()
def recommended():
    locale = request.args.get("locale", "en")
    return success(service.recommended(current_user(), locale if locale in {"en", "ar"} else "en"))


@api_v1.get("/alternatives/saved", tags=[TAG_ALTERNATIVES], summary="Saved alternatives")
@jwt_required()
def saved():
    return success(service.list_saved(current_user()))


@api_v1.post(
    "/alternatives/<int:id>/save",
    tags=[TAG_ALTERNATIVES],
    summary="Save, accept, or dismiss an alternative",
)
@jwt_required()
def save_alternative(path: IdPath, body: SaveAlternativeBody):
    return success(service.set_status(current_user(), path.id, body.status), 201)
