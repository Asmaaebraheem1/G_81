"""Document endpoints (multipart uploads and private downloads)."""

from __future__ import annotations

from flask import request
from flask_jwt_extended import jwt_required

from app.api.v1.blueprint import TAG_DOCUMENTS, api_v1
from app.api.v1.deps import current_user
from app.api.v1.schemas import DocumentConfirmBody, IdPath
from app.core.errors import success
from app.modules.documents import service


@api_v1.post("/documents", tags=[TAG_DOCUMENTS], summary="Upload a private document")
@jwt_required()
def upload_document():
    consent_raw = (request.form.get("consent") or "").strip().lower()
    consent = consent_raw in {"1", "true", "yes", "on"}
    return success(service.upload(current_user(), request.files.get("file"), consent), 201)


@api_v1.get("/documents", tags=[TAG_DOCUMENTS], summary="List own documents")
@jwt_required()
def list_documents():
    return success(service.list_documents(current_user(), request.args.get("status")))


@api_v1.get("/documents/<int:id>", tags=[TAG_DOCUMENTS], summary="Document metadata")
@jwt_required()
def document_detail(path: IdPath):
    return success(service.get_document(current_user(), path.id))


@api_v1.get(
    "/documents/<int:id>/download",
    tags=[TAG_DOCUMENTS],
    summary="Authenticated download",
)
@jwt_required()
def document_download(path: IdPath):
    return service.download(current_user(), path.id)


@api_v1.post(
    "/documents/<int:id>/extract",
    tags=[TAG_DOCUMENTS],
    summary="Best-effort AI extraction",
)
@jwt_required()
def document_extract(path: IdPath):
    return success(service.extract(current_user(), path.id))


@api_v1.post(
    "/documents/<int:id>/confirm",
    tags=[TAG_DOCUMENTS],
    summary="Confirm values and create a record",
)
@jwt_required()
def document_confirm(path: IdPath, body: DocumentConfirmBody):
    return success(service.confirm(current_user(), path.id, body), 201)


@api_v1.delete("/documents/<int:id>", tags=[TAG_DOCUMENTS], summary="Delete an unlinked document")
@jwt_required()
def document_delete(path: IdPath):
    return success(service.delete(current_user(), path.id))
