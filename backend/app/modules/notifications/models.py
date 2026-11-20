"""Notification and notification preference models."""

from __future__ import annotations

from app.core.db import TimestampMixin, db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    type = db.Column(db.String(30), nullable=False, index=True)
    title_en = db.Column(db.String(200), nullable=False)
    title_ar = db.Column(db.String(200), nullable=False)
    body_en = db.Column(db.Text, nullable=False)
    body_ar = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    action_url = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", backref=db.backref("notifications", lazy="dynamic"))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "title_en": self.title_en,
            "title_ar": self.title_ar,
            "body_en": self.body_en,
            "body_ar": self.body_ar,
            "is_read": self.is_read,
            "action_url": self.action_url,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }


class NotificationPreference(db.Model, TimestampMixin):
    __tablename__ = "notification_preferences"
    __table_args__ = (db.UniqueConstraint("user_id", "type", name="uq_notification_preference"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    type = db.Column(db.String(30), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, default=True)

    user = db.relationship("User", backref=db.backref("notification_preferences", lazy="dynamic"))
