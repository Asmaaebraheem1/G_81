"""Emission category and factor models."""

from __future__ import annotations

from app.core.db import TimestampMixin, db


class EmissionCategory(db.Model, TimestampMixin):
    __tablename__ = "emission_categories"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False, index=True)
    name_en = db.Column(db.String(120), nullable=False)
    name_ar = db.Column(db.String(120), nullable=False)
    description_en = db.Column(db.Text, nullable=True)
    description_ar = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(60), nullable=True)
    color_hex = db.Column(db.String(9), nullable=True)
    unit_hint = db.Column(db.String(40), nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0, index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    factors = db.relationship("EmissionFactor", back_populates="category", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "name_en": self.name_en,
            "name_ar": self.name_ar,
            "description_en": self.description_en,
            "description_ar": self.description_ar,
            "icon": self.icon,
            "color_hex": self.color_hex,
            "unit_hint": self.unit_hint,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
        }


class EmissionFactor(db.Model, TimestampMixin):
    __tablename__ = "emission_factors"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(
        db.Integer, db.ForeignKey("emission_categories.id"), nullable=False, index=True
    )
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name_en = db.Column(db.String(160), nullable=False)
    name_ar = db.Column(db.String(160), nullable=False)
    activity_type = db.Column(db.String(80), nullable=False, index=True)
    unit = db.Column(db.String(30), nullable=False)
    factor_grams_co2e = db.Column(db.Integer, nullable=False)
    source_name = db.Column(db.String(200), nullable=False)
    source_url = db.Column(db.String(500), nullable=True)
    source_year = db.Column(db.Integer, nullable=True)
    region = db.Column(db.String(80), nullable=False, default="GLOBAL", index=True)
    valid_from = db.Column(db.Date, nullable=False)
    valid_to = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    notes = db.Column(db.Text, nullable=True)

    category = db.relationship("EmissionCategory", back_populates="factors")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category_id": self.category_id,
            "key": self.key,
            "name_en": self.name_en,
            "name_ar": self.name_ar,
            "activity_type": self.activity_type,
            "unit": self.unit,
            "factor_grams_co2e": self.factor_grams_co2e,
            "factor_kg_co2e": round(self.factor_grams_co2e / 1000, 6),
            "source_name": self.source_name,
            "source_url": self.source_url,
            "source_year": self.source_year,
            "region": self.region,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_to": self.valid_to.isoformat() if self.valid_to else None,
            "is_active": self.is_active,
            "notes": self.notes,
        }
