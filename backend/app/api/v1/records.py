"""Consumption record endpoints."""

from __future__ import annotations

from flask_jwt_extended import jwt_required

from app.api.v1.blueprint import TAG_RECORDS, api_v1
from app.api.v1.deps import current_user
from app.api.v1.schemas import IdPath, RecordCreate, RecordQuery, RecordUpdate
from app.core.errors import success
from app.modules.records import service


@api_v1.get("/records", tags=[TAG_RECORDS], summary="List records")
@jwt_required()
def list_records(query: RecordQuery):
    # The paginated envelope already contains top-level data + meta.
    return service.list_records(current_user(), query)


@api_v1.post("/records", tags=[TAG_RECORDS], summary="Create a record + calculate")
@jwt_required()
def create_record(body: RecordCreate):
    return success(service.create_record(current_user(), body), 201)


@api_v1.get("/records/<int:id>", tags=[TAG_RECORDS], summary="Record detail + formula")
@jwt_required()
def get_record(path: IdPath):
    return success(service.get_record(current_user(), path.id).to_dict())


@api_v1.patch("/records/<int:id>", tags=[TAG_RECORDS], summary="Edit a record")
@jwt_required()
def update_record(path: IdPath, body: RecordUpdate):
    return success(service.update_record(current_user(), path.id, body))


@api_v1.delete("/records/<int:id>", tags=[TAG_RECORDS], summary="Soft delete a record")
@jwt_required()
def delete_record(path: IdPath):
    return success(service.delete_record(current_user(), path.id))


@api_v1.get(
    "/records/<int:id>/calculation",
    tags=[TAG_RECORDS],
    summary="Formula breakdown",
)
@jwt_required()
def record_calculation(path: IdPath):
    return success(service.calculation(current_user(), path.id))
