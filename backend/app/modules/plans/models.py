"""Reduction plan and action models."""

from __future__ import annotations

from app.core.db import TimestampMixin, db


class ReductionPlan(db.Model, TimestampMixin):
    __tablename__ = "reduction_plans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey("organizations.id"), nullable=True, index=True
    )
    goal_id = db.Column(db.Integer, db.ForeignKey("goals.id"), nullable=True, index=True)
    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    locale = db.Column(db.String(5), nullable=False, default="en")
    source = db.Column(db.String(20), nullable=False, default="ai")
    model = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="draft", index=True)
    generated_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", backref=db.backref("plans", lazy="dynamic"))
    organization = db.relationship("Organization")
    goal = db.relationship("Goal", back_populates="plans")
    actions = db.relationship(
        "PlanAction",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="PlanAction.sort_order",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "goal_id": self.goal_id,
            "title": self.title,
            "summary": self.summary,
            "locale": self.locale,
            "source": self.source,
            "model": self.model,
            "status": self.status,
            "generated_at": self.generated_at.isoformat() + "Z" if self.generated_at else None,
            "actions": [action.to_dict() for action in self.actions],
        }


class PlanAction(db.Model, TimestampMixin):
    __tablename__ = "plan_actions"

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("reduction_plans.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(
        db.Integer, db.ForeignKey("emission_categories.id"), nullable=True, index=True
    )
    priority = db.Column(db.String(10), nullable=False, default="medium", index=True)
    timeframe = db.Column(db.String(20), nullable=False, default="this_month")
    estimated_saving_grams = db.Column(db.Integer, nullable=True)
    saving_assumption = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    due_date = db.Column(db.Date, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    plan = db.relationship("ReductionPlan", back_populates="actions")
    category = db.relationship("EmissionCategory")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "title": self.title,
            "description": self.description,
            "category_id": self.category_id,
            "priority": self.priority,
            "timeframe": self.timeframe,
            "estimated_saving_grams": self.estimated_saving_grams,
            "estimated_saving_kg": round((self.estimated_saving_grams or 0) / 1000, 2),
            "saving_assumption": self.saving_assumption,
            "status": self.status,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat() + "Z" if self.completed_at else None,
        }
