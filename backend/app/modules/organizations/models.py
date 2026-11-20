"""Organization model."""

from __future__ import annotations

from app.core.db import TimestampMixin, db


class Organization(db.Model, TimestampMixin):
    __tablename__ = "organizations"

    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String(200), nullable=False)
    name_ar = db.Column(db.String(200), nullable=True)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    org_type = db.Column(db.String(40), nullable=False, default="business")
    industry = db.Column(db.String(120), nullable=True)
    country = db.Column(db.String(80), nullable=True)
    city = db.Column(db.String(120), nullable=True)
    size = db.Column(db.String(40), nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)
    is_verified = db.Column(db.Boolean, nullable=False, default=False, index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    users = db.relationship("User", back_populates="organization", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name_en": self.name_en,
            "name_ar": self.name_ar,
            "slug": self.slug,
            "org_type": self.org_type,
            "industry": self.industry,
            "country": self.country,
            "city": self.city,
            "size": self.size,
            "contact_email": self.contact_email,
            "is_verified": self.is_verified,
            "is_active": self.is_active,
        }
