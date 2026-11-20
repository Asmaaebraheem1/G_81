"""Sustainability goal model."""

from __future__ import annotations

from app.core.db import TimestampMixin, db


class Goal(db.Model, TimestampMixin):
    __tablename__ = "goals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey("organizations.id"), nullable=True, index=True
    )
    title = db.Column(db.String(200), nullable=False)
    target_percent = db.Column(db.Numeric(5, 2), nullable=False)
    period_type = db.Column(db.String(10), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False, index=True)
    baseline_start = db.Column(db.Date, nullable=False)
    baseline_end = db.Column(db.Date, nullable=False)
    baseline_emissions_grams = db.Column(db.Integer, nullable=False)
    target_emissions_grams = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active", index=True)

    user = db.relationship("User", backref=db.backref("goals", lazy="dynamic"))
    organization = db.relationship("Organization")
    plans = db.relationship("ReductionPlan", back_populates="goal", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "title": self.title,
            "target_percent": float(self.target_percent),
            "period_type": self.period_type,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "baseline_start": self.baseline_start.isoformat(),
            "baseline_end": self.baseline_end.isoformat(),
            "baseline_emissions_grams": self.baseline_emissions_grams,
            "target_emissions_grams": self.target_emissions_grams,
            "status": self.status,
        }
