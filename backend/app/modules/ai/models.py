"""AI conversation, usage, flagged-response, and cache models."""

from __future__ import annotations

from app.core.db import TimestampMixin, db


class AiConversation(db.Model, TimestampMixin):
    __tablename__ = "ai_conversations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)

    user = db.relationship("User", backref=db.backref("ai_conversations", lazy="dynamic"))
    messages = db.relationship(
        "AiMessage", back_populates="conversation", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
        }


class AiMessage(db.Model):
    __tablename__ = "ai_messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("ai_conversations.id"), nullable=False, index=True
    )
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    locale = db.Column(db.String(5), nullable=False, default="en")
    model = db.Column(db.String(200), nullable=True)
    tokens = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, index=True)

    conversation = db.relationship("AiConversation", back_populates="messages")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "locale": self.locale,
            "model": self.model,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }


class AiUsage(db.Model):
    __tablename__ = "ai_usage"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    feature = db.Column(db.String(40), nullable=False, index=True)
    model = db.Column(db.String(200), nullable=False)
    prompt_tokens = db.Column(db.Integer, nullable=False, default=0)
    completion_tokens = db.Column(db.Integer, nullable=False, default=0)
    total_tokens = db.Column(db.Integer, nullable=False, default=0)
    latency_ms = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(30), nullable=False, default="success", index=True)
    error_code = db.Column(db.String(60), nullable=True)
    request_hash = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, index=True)

    user = db.relationship("User")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "feature": self.feature,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
            "status": self.status,
            "error_code": self.error_code,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }


class AiFlaggedResponse(db.Model):
    __tablename__ = "ai_flagged_responses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    message_id = db.Column(db.Integer, db.ForeignKey("ai_messages.id"), nullable=True)
    reason = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="open", index=True)
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User")
    message = db.relationship("AiMessage")


class AiCache(db.Model):
    __tablename__ = "ai_cache"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    cache_key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    feature = db.Column(db.String(40), nullable=False)
    locale = db.Column(db.String(5), nullable=False, default="en")
    response_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)

    user = db.relationship("User")
