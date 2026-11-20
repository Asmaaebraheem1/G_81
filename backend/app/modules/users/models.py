"""User, profile, and refresh-token models."""

from __future__ import annotations

from app.core.db import TimestampMixin, db


class User(db.Model, TimestampMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    account_type = db.Column(db.String(30), nullable=False, default="individual", index=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey("organizations.id"), nullable=True, index=True
    )
    is_org_owner = db.Column(db.Boolean, nullable=False, default=False)
    locale = db.Column(db.String(5), nullable=False, default="ar")
    timezone = db.Column(db.String(64), nullable=False, default="UTC")
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    last_login_at = db.Column(db.DateTime, nullable=True)

    organization = db.relationship("Organization", back_populates="users")
    profile = db.relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    refresh_tokens = db.relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "account_type": self.account_type,
            "organization_id": self.organization_id,
            "is_org_owner": self.is_org_owner,
            "locale": self.locale,
            "timezone": self.timezone,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "last_login_at": self.last_login_at.isoformat() + "Z" if self.last_login_at else None,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
        }


class UserProfile(db.Model, TimestampMixin):
    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True
    )
    phone = db.Column(db.String(40), nullable=True)
    country = db.Column(db.String(80), nullable=True)
    city = db.Column(db.String(120), nullable=True)
    household_size = db.Column(db.Integer, nullable=True)
    home_type = db.Column(db.String(40), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    avatar_path = db.Column(db.String(500), nullable=True)
    leaderboard_opt_in = db.Column(db.Boolean, nullable=False, default=False, index=True)
    leaderboard_alias = db.Column(db.String(80), nullable=True)
    onboarding_completed = db.Column(db.Boolean, nullable=False, default=False)
    default_period = db.Column(db.String(10), nullable=False, default="month")

    user = db.relationship("User", back_populates="profile")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "phone": self.phone,
            "country": self.country,
            "city": self.city,
            "household_size": self.household_size,
            "home_type": self.home_type,
            "bio": self.bio,
            "avatar_path": self.avatar_path,
            "leaderboard_opt_in": self.leaderboard_opt_in,
            "leaderboard_alias": self.leaderboard_alias,
            "onboarding_completed": self.onboarding_completed,
            "default_period": self.default_period,
        }


class RefreshToken(db.Model):
    __tablename__ = "refresh_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    token_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False)

    user = db.relationship("User", back_populates="refresh_tokens")
