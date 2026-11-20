"""Sustainable alternative and saved-alternative models."""

from __future__ import annotations

from app.core.db import TimestampMixin, db


class Alternative(db.Model, TimestampMixin):
    __tablename__ = "alternatives"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    title_en = db.Column(db.String(200), nullable=False)
    title_ar = db.Column(db.String(200), nullable=False)
    description_en = db.Column(db.Text, nullable=False)
    description_ar = db.Column(db.Text, nullable=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey("emission_categories.id"), nullable=True, index=True
    )
    estimated_reduction_percent = db.Column(db.Numeric(5, 2), nullable=False)
    assumption_en = db.Column(db.Text, nullable=False)
    assumption_ar = db.Column(db.Text, nullable=False)
    source_name = db.Column(db.String(200), nullable=True)
    source_url = db.Column(db.String(500), nullable=True)
    icon = db.Column(db.String(60), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    category = db.relationship("EmissionCategory")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "title_en": self.title_en,
            "title_ar": self.title_ar,
            "description_en": self.description_en,
            "description_ar": self.description_ar,
            "category_id": self.category_id,
            "estimated_reduction_percent": float(self.estimated_reduction_percent),
            "assumption_en": self.assumption_en,
            "assumption_ar": self.assumption_ar,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "icon": self.icon,
            "is_active": self.is_active,
        }


class SavedAlternative(db.Model, TimestampMixin):
    __tablename__ = "saved_alternatives"
    __table_args__ = (
        db.UniqueConstraint("user_id", "alternative_id", name="uq_saved_alternative"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    alternative_id = db.Column(
        db.Integer, db.ForeignKey("alternatives.id"), nullable=False, index=True
    )
    status = db.Column(db.String(20), nullable=False, default="saved", index=True)

    user = db.relationship("User", backref=db.backref("saved_alternatives", lazy="dynamic"))
    alternative = db.relationship("Alternative")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "alternative_id": self.alternative_id,
            "status": self.status,
            "alternative": self.alternative.to_dict() if self.alternative else None,
        }
