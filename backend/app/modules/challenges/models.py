"""Challenge, participation, badge, and points models."""

from __future__ import annotations

from app.core.db import TimestampMixin, db


class Badge(db.Model, TimestampMixin):
    __tablename__ = "badges"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False, index=True)
    title_en = db.Column(db.String(160), nullable=False)
    title_ar = db.Column(db.String(160), nullable=False)
    description_en = db.Column(db.Text, nullable=False)
    description_ar = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(60), nullable=True)
    criteria = db.Column(db.Text, nullable=False)
    points = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "title_en": self.title_en,
            "title_ar": self.title_ar,
            "description_en": self.description_en,
            "description_ar": self.description_ar,
            "icon": self.icon,
            "criteria": self.criteria,
            "points": self.points,
        }


class Challenge(db.Model, TimestampMixin):
    __tablename__ = "challenges"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    title_en = db.Column(db.String(200), nullable=False)
    title_ar = db.Column(db.String(200), nullable=False)
    description_en = db.Column(db.Text, nullable=False)
    description_ar = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), nullable=False, default="weekly", index=True)
    category_id = db.Column(
        db.Integer, db.ForeignKey("emission_categories.id"), nullable=True, index=True
    )
    target_type = db.Column(db.String(40), nullable=False)
    target_value = db.Column(db.Numeric(10, 2), nullable=False)
    points = db.Column(db.Integer, nullable=False, default=0)
    badge_id = db.Column(db.Integer, db.ForeignKey("badges.id"), nullable=True)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False, index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)

    category = db.relationship("EmissionCategory")
    badge = db.relationship("Badge")
    participants = db.relationship(
        "ChallengeParticipant", back_populates="challenge", lazy="dynamic"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "title_en": self.title_en,
            "title_ar": self.title_ar,
            "description_en": self.description_en,
            "description_ar": self.description_ar,
            "type": self.type,
            "category_id": self.category_id,
            "target_type": self.target_type,
            "target_value": float(self.target_value),
            "points": self.points,
            "badge_id": self.badge_id,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "is_active": self.is_active,
        }


class ChallengeParticipant(db.Model, TimestampMixin):
    __tablename__ = "challenge_participants"
    __table_args__ = (
        db.UniqueConstraint("challenge_id", "user_id", name="uq_challenge_participant"),
    )

    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    progress_value = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="joined", index=True)
    joined_at = db.Column(db.DateTime, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    challenge = db.relationship("Challenge", back_populates="participants")
    user = db.relationship("User", backref=db.backref("challenge_participations", lazy="dynamic"))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "challenge_id": self.challenge_id,
            "user_id": self.user_id,
            "progress_value": float(self.progress_value),
            "status": self.status,
            "joined_at": self.joined_at.isoformat() + "Z" if self.joined_at else None,
            "completed_at": self.completed_at.isoformat() + "Z" if self.completed_at else None,
        }


class UserBadge(db.Model):
    __tablename__ = "user_badges"
    __table_args__ = (db.UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    badge_id = db.Column(db.Integer, db.ForeignKey("badges.id"), nullable=False, index=True)
    awarded_at = db.Column(db.DateTime, nullable=False)

    user = db.relationship("User", backref=db.backref("user_badges", lazy="dynamic"))
    badge = db.relationship("Badge")


class PointsLedger(db.Model):
    __tablename__ = "points_ledger"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    points = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    reference_type = db.Column(db.String(40), nullable=True)
    reference_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, index=True)

    user = db.relationship("User", backref=db.backref("points_entries", lazy="dynamic"))
