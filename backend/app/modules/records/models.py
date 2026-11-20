"""Consumption record model."""

from __future__ import annotations

from app.core.db import TimestampMixin, db


class ConsumptionRecord(db.Model, TimestampMixin):
    __tablename__ = "consumption_records"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey("organizations.id"), nullable=True, index=True
    )
    category_id = db.Column(
        db.Integer, db.ForeignKey("emission_categories.id"), nullable=False, index=True
    )
    factor_id = db.Column(
        db.Integer, db.ForeignKey("emission_factors.id"), nullable=False, index=True
    )
    activity_date = db.Column(db.Date, nullable=False, index=True)
    quantity = db.Column(db.Numeric(14, 4), nullable=False)
    unit = db.Column(db.String(30), nullable=False)
    factor_grams_co2e_snapshot = db.Column(db.Integer, nullable=False)
    factor_source_snapshot = db.Column(db.String(300), nullable=False)
    emissions_grams = db.Column(db.Integer, nullable=False, index=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="active", index=True)
    source = db.Column(db.String(20), nullable=False, default="manual")
    document_id = db.Column(db.Integer, nullable=True, unique=True, index=True)

    user = db.relationship("User", backref=db.backref("records", lazy="dynamic"))
    organization = db.relationship("Organization")
    category = db.relationship("EmissionCategory")
    factor = db.relationship("EmissionFactor")
    document = db.relationship(
        "Document",
        back_populates="record",
        uselist=False,
        foreign_keys="Document.record_id",
    )

    @property
    def emissions_kg(self) -> float:
        return round(self.emissions_grams / 1000, 2)

    @property
    def formula(self) -> str:
        quantity = float(self.quantity)
        return (
            f"{quantity:g} {self.unit} × {self.factor_grams_co2e_snapshot} g CO2e/"
            f"{self.unit} = {self.emissions_grams:,} g CO2e "
            f"({self.emissions_kg:.2f} kg)"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "category": self.category.to_dict() if self.category else None,
            "factor": self.factor.to_dict() if self.factor else None,
            "activity_date": self.activity_date.isoformat() if self.activity_date else None,
            "quantity": float(self.quantity),
            "unit": self.unit,
            "factor_grams_co2e_snapshot": self.factor_grams_co2e_snapshot,
            "factor_source_snapshot": self.factor_source_snapshot,
            "emissions_grams": self.emissions_grams,
            "emissions_kg": self.emissions_kg,
            "formula": self.formula,
            "notes": self.notes,
            "status": self.status,
            "source": self.source,
            "document_id": self.document_id,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }
