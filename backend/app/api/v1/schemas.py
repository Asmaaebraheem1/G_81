"""Pydantic v2 request models for the public API."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class IdPath(Strict):
    id: int = Field(gt=0)


class PlanActionPath(Strict):
    id: int = Field(gt=0)
    action_id: int = Field(gt=0)


class SlugPath(Strict):
    slug: str = Field(min_length=1, max_length=200)


class FactorQuery(Strict):
    category_id: int | None = None
    q: str | None = None


class AlternativeQuery(Strict):
    category_id: int | None = None


class ArticleQuery(Strict):
    category: str | None = None
    q: str | None = None


class RegisterBody(Strict):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=200)
    account_type: Literal["individual", "household", "organization"] = "individual"
    organization_name: str | None = Field(default=None, max_length=200)
    locale: Literal["en", "ar"] = "ar"
    timezone: str = "UTC"
    household_size: int | None = Field(default=None, ge=1, le=50)


class LoginBody(Strict):
    email: EmailStr
    password: str


class LogoutBody(Strict):
    refresh_token: str | None = None
    all_devices: bool = False


class UpdateMeBody(Strict):
    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    locale: Literal["en", "ar"] | None = None
    timezone: str | None = None


class ChangePasswordBody(Strict):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class ProfileBody(Strict):
    phone: str | None = Field(default=None, max_length=40)
    country: str | None = Field(default=None, max_length=80)
    city: str | None = Field(default=None, max_length=120)
    household_size: int | None = Field(default=None, ge=1, le=50)
    home_type: Literal["apartment", "house", "other"] | None = None
    bio: str | None = Field(default=None, max_length=1000)
    leaderboard_opt_in: bool | None = None
    leaderboard_alias: str | None = Field(default=None, max_length=80)
    onboarding_completed: bool | None = None
    default_period: Literal["week", "month", "year"] | None = None


class OrganizationBody(Strict):
    name_en: str | None = Field(default=None, min_length=2, max_length=200)
    name_ar: str | None = Field(default=None, max_length=200)
    org_type: Literal["business", "ngo", "government", "other"] | None = None
    industry: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=80)
    city: str | None = Field(default=None, max_length=120)
    size: Literal["1-10", "11-50", "51-200", "200+"] | None = None
    contact_email: EmailStr | None = None


class RecordCreate(Strict):
    category_id: int = Field(gt=0)
    factor_id: int = Field(gt=0)
    activity_date: date
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=30)
    notes: str | None = Field(default=None, max_length=1000)


class RecordUpdate(Strict):
    category_id: int | None = Field(default=None, gt=0)
    factor_id: int | None = Field(default=None, gt=0)
    activity_date: date | None = None
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, min_length=1, max_length=30)
    notes: str | None = Field(default=None, max_length=1000)


class RecordQuery(Strict):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=50)
    q: str | None = None
    category_id: int | None = None
    from_date: str | None = Field(default=None, alias="from")
    to_date: str | None = Field(default=None, alias="to")
    sort: Literal["-activity_date", "activity_date", "-emissions_grams", "emissions_grams"] = (
        "-activity_date"
    )


class ReportQuery(Strict):
    period: Literal["week", "month", "year", "last_7_days", "last_30_days", "all"] = "month"
    from_date: str | None = Field(default=None, alias="from")
    to_date: str | None = Field(default=None, alias="to")


class TrendQuery(Strict):
    months: int = Field(default=6, ge=1, le=24)


class TopActivitiesQuery(Strict):
    period: Literal["week", "month", "year", "last_7_days", "last_30_days", "all"] = "month"
    from_date: str | None = Field(default=None, alias="from")
    to_date: str | None = Field(default=None, alias="to")
    limit: int = Field(default=5, ge=1, le=20)


class ExportQuery(Strict):
    from_date: str = Field(alias="from")
    to_date: str = Field(alias="to")


class GoalCreate(Strict):
    title: str = Field(min_length=2, max_length=200)
    target_percent: float = Field(gt=0, le=100)
    period_type: Literal["weekly", "monthly", "yearly"]
    start_date: date
    end_date: date
    baseline_start: date | None = None
    baseline_end: date | None = None


class GoalUpdate(Strict):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    start_date: date | None = None
    end_date: date | None = None
    status: Literal["active", "completed", "missed", "cancelled"] | None = None


class PlanGenerate(Strict):
    goal_id: int | None = Field(default=None, gt=0)
    period: Literal["week", "month", "year", "last_30_days"] = "month"
    locale: Literal["en", "ar"] = "en"


class PlanUpdate(Strict):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    status: Literal["draft", "active", "completed", "archived"] | None = None


class PlanActionUpdate(Strict):
    status: Literal["pending", "in_progress", "completed", "skipped"]


class SaveAlternativeBody(Strict):
    status: Literal["saved", "accepted", "dismissed"] = "saved"


class ChallengeProgressBody(Strict):
    value: float | None = Field(default=None, ge=0)
    note: str | None = Field(default=None, max_length=500)


class PreferenceItem(Strict):
    type: Literal[
        "reminder",
        "goal",
        "alert",
        "plan",
        "challenge",
        "summary",
        "announcement",
    ]
    enabled: bool


class PreferencesUpdate(Strict):
    preferences: list[PreferenceItem]


class ChatBody(Strict):
    message: str = Field(min_length=2, max_length=2000)
    conversation_id: int | None = Field(default=None, gt=0)
    locale: Literal["en", "ar"] = "en"


class InsightsBody(Strict):
    period: Literal["week", "month", "year", "last_30_days"] = "month"
    from_date: date | None = None
    to_date: date | None = None
    locale: Literal["en", "ar"] = "en"


class SummaryBody(Strict):
    period: Literal["week", "month", "year", "last_30_days"] = "month"
    locale: Literal["en", "ar"] = "en"


class FlagBody(Strict):
    message_id: int = Field(gt=0)
    reason: Literal["inaccurate", "unsafe", "offensive", "other"] = "inaccurate"
    notes: str | None = Field(default=None, max_length=1000)


class DocumentConfirmBody(Strict):
    vendor: str | None = Field(default=None, max_length=200)
    activity_date: date
    category_id: int = Field(gt=0)
    factor_id: int = Field(gt=0)
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=30)
    notes: str | None = Field(default=None, max_length=1000)
