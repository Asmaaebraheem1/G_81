"""Private document upload, metadata, download, extraction, and confirmation."""

from __future__ import annotations

import io
import os
import uuid
from pathlib import Path

from flask import current_app, send_file
from PIL import Image
from werkzeug.utils import secure_filename

from app.core.db import db
from app.core.errors import ApiError
from app.modules.documents.models import Document
from app.modules.records.service import create_record
from app.modules.users.models import User

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}


def _root() -> Path:
    return Path(current_app.config["UPLOAD_FOLDER"]).resolve()


def _detect_mime(data: bytes) -> tuple[str, str]:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", ".png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp", ".webp"
    if data.startswith(b"%PDF"):
        return "application/pdf", ".pdf"
    raise ApiError(
        "unsupported_file_type",
        "Only JPG, PNG, WebP, and PDF files are accepted.",
        422,
    )


def _verify_image(data: bytes) -> None:
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.verify()
    except Exception as exc:  # noqa: BLE001
        raise ApiError(
            "unsupported_file_type",
            "The image could not be verified.",
            422,
        ) from exc


def _owned(user: User, document_id: int) -> Document:
    document = Document.query.filter_by(id=document_id, user_id=user.id).first()
    if document is None:
        raise ApiError("not_found", "Document not found.", 404)
    return document


def upload(user: User, file_storage, consent: bool) -> dict:
    if file_storage is None or not file_storage.filename:
        raise ApiError("validation_error", "A file is required.", 422)
    original = secure_filename(file_storage.filename) or "upload"
    extension = Path(original).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ApiError(
            "unsupported_file_type",
            "Only JPG, PNG, WebP, and PDF files are accepted.",
            422,
        )
    data = file_storage.read()
    max_bytes = int(current_app.config.get("MAX_IMAGE_BYTES", 10 * 1024 * 1024))
    if len(data) == 0:
        raise ApiError("validation_error", "The uploaded file is empty.", 422)
    if len(data) > max_bytes:
        raise ApiError(
            "upload_too_large",
            "Each file must be 10 MB or smaller.",
            413,
        )
    mime, detected_ext = _detect_mime(data)
    if mime.startswith("image/"):
        _verify_image(data)
    stored_name = f"{uuid.uuid4().hex}{detected_ext}"
    relative = Path(str(user.id)) / stored_name
    destination = _root() / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    try:
        os.chmod(destination, 0o600)
    except OSError:
        pass
    document = Document(
        user_id=user.id,
        organization_id=user.organization_id if user.account_type == "organization" else None,
        original_filename=original,
        stored_filename=stored_name,
        mime_type=mime,
        size_bytes=len(data),
        storage_path=str(relative).replace("\\", "/"),
        status="uploaded",
        ai_consent=bool(consent),
    )
    db.session.add(document)
    db.session.commit()
    result = document.to_dict()
    result["download_url"] = f"/api/v1/documents/{document.id}/download"
    return result


def list_documents(user: User, status: str | None = None) -> list[dict]:
    query = Document.query.filter_by(user_id=user.id)
    if status:
        query = query.filter_by(status=status)
    return [document.to_dict() for document in query.order_by(Document.created_at.desc()).all()]


def get_document(user: User, document_id: int) -> dict:
    document = _owned(user, document_id)
    data = document.to_dict()
    data["download_url"] = f"/api/v1/documents/{document.id}/download"
    return data


def download(user: User, document_id: int):
    document = _owned(user, document_id)
    root = _root()
    path = (root / document.storage_path).resolve()
    if root not in path.parents or not path.exists():
        raise ApiError("not_found", "The stored file could not be found.", 404)
    return send_file(
        path,
        mimetype=document.mime_type,
        as_attachment=True,
        download_name=document.original_filename,
    )


def extract(user: User, document_id: int) -> dict:
    from app.modules.ai import service as ai_service

    document = _owned(user, document_id)
    if document.record_id is not None:
        raise ApiError("conflict", "This document is already linked to a record.", 409)
    if document.status == "extracting":
        raise ApiError("conflict", "Extraction is already running.", 409)
    document.status = "extracting"
    db.session.commit()
    return ai_service.extract_document(user, document)


def confirm(user: User, document_id: int, payload) -> dict:
    document = _owned(user, document_id)
    if document.record_id is not None:
        raise ApiError("conflict", "This document is already linked to a record.", 409)
    if document.status not in {"uploaded", "extracted", "failed", "rejected"}:
        raise ApiError("conflict", "This document cannot be confirmed in its current state.", 409)
    notes = payload.notes
    if not notes and payload.vendor:
        notes = f"Vendor: {payload.vendor}"

    class _Payload:
        pass

    body = _Payload()
    body.category_id = payload.category_id
    body.factor_id = payload.factor_id
    body.activity_date = payload.activity_date
    body.quantity = payload.quantity
    body.unit = payload.unit
    body.notes = notes
    record = create_record(user, body, source="document", document=document)
    return {"document": document.to_dict(), "record": record}


def delete(user: User, document_id: int) -> dict:
    document = _owned(user, document_id)
    if document.record_id is not None:
        raise ApiError(
            "conflict",
            "Delete the linked record before deleting this document.",
            409,
        )
    root = _root()
    path = (root / document.storage_path).resolve()
    if root in path.parents and path.exists():
        try:
            path.unlink()
        except OSError:
            pass
    db.session.delete(document)
    db.session.commit()
    return {"deleted": True, "id": document_id}
