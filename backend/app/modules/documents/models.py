"""Uploaded document model."""

from __future__ import annotations

from app.core.db import TimestampMixin, db


class Document(db.Model, TimestampMixin):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey("organizations.id"), nullable=True, index=True
    )
    record_id = db.Column(
        db.Integer,
        db.ForeignKey("consumption_records.id"),
        unique=True,
        nullable=True,
        index=True,
    )
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="uploaded", index=True)
    ai_consent = db.Column(db.Boolean, nullable=False, default=False)
    extraction_json = db.Column(db.Text, nullable=True)
    extraction_model = db.Column(db.String(200), nullable=True)
    confirmed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", backref=db.backref("documents", lazy="dynamic"))
    organization = db.relationship("Organization")
    record = db.relationship(
        "ConsumptionRecord",
        back_populates="document",
        uselist=False,
        foreign_keys=[record_id],
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "record_id": self.record_id,
            "original_filename": self.original_filename,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "status": self.status,
            "ai_consent": self.ai_consent,
            "extraction_model": self.extraction_model,
            "confirmed_at": self.confirmed_at.isoformat() + "Z" if self.confirmed_at else None,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }
