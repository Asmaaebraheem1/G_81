"""Educational article model."""

from __future__ import annotations

from app.core.db import TimestampMixin, db


class Article(db.Model, TimestampMixin):
    __tablename__ = "articles"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    title_en = db.Column(db.String(250), nullable=False)
    title_ar = db.Column(db.String(250), nullable=False)
    summary_en = db.Column(db.Text, nullable=True)
    summary_ar = db.Column(db.Text, nullable=True)
    body_en = db.Column(db.Text, nullable=False)
    body_ar = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(500), nullable=True)
    category = db.Column(db.String(80), nullable=True, index=True)
    is_published = db.Column(db.Boolean, nullable=False, default=False, index=True)
    published_at = db.Column(db.DateTime, nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "slug": self.slug,
            "title_en": self.title_en,
            "title_ar": self.title_ar,
            "summary_en": self.summary_en,
            "summary_ar": self.summary_ar,
            "body_en": self.body_en,
            "body_ar": self.body_ar,
            "image_path": self.image_path,
            "category": self.category,
            "is_published": self.is_published,
            "published_at": self.published_at.isoformat() + "Z" if self.published_at else None,
        }
