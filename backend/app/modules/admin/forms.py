"""WTForms used by the Jinja admin panel."""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import URL, DataRequired, Email, Length, NumberRange, Optional


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign in")


class CategoryForm(FlaskForm):
    key = StringField("Key", validators=[DataRequired(), Length(max=80)])
    name_en = StringField("Name (EN)", validators=[DataRequired(), Length(max=120)])
    name_ar = StringField("Name (AR)", validators=[DataRequired(), Length(max=120)])
    description_en = TextAreaField("Description (EN)", validators=[Optional()])
    description_ar = TextAreaField("Description (AR)", validators=[Optional()])
    icon = StringField("Icon key", validators=[Optional(), Length(max=60)])
    color_hex = StringField("Color", validators=[Optional(), Length(max=9)])
    unit_hint = StringField("Unit hint", validators=[Optional(), Length(max=40)])
    sort_order = IntegerField("Sort order", default=0)
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save category")


class FactorForm(FlaskForm):
    category_id = SelectField("Category", coerce=int, validators=[DataRequired()])
    key = StringField("Key", validators=[DataRequired(), Length(max=100)])
    name_en = StringField("Name (EN)", validators=[DataRequired(), Length(max=160)])
    name_ar = StringField("Name (AR)", validators=[DataRequired(), Length(max=160)])
    activity_type = StringField("Activity type", validators=[DataRequired(), Length(max=80)])
    unit = StringField("Unit", validators=[DataRequired(), Length(max=30)])
    factor_grams_co2e = IntegerField(
        "Factor (g CO2e per unit)", validators=[DataRequired(), NumberRange(min=0)]
    )
    source_name = StringField("Source name", validators=[DataRequired(), Length(max=200)])
    source_url = StringField("Source URL", validators=[Optional(), URL(), Length(max=500)])
    source_year = IntegerField(
        "Source year", validators=[Optional(), NumberRange(min=1990, max=2100)]
    )
    region = StringField("Region", validators=[DataRequired(), Length(max=80)])
    valid_from = DateField("Valid from", validators=[DataRequired()])
    valid_to = DateField("Valid to", validators=[Optional()])
    is_active = BooleanField("Active", default=True)
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Save factor")


class ArticleForm(FlaskForm):
    slug = StringField("Slug", validators=[DataRequired(), Length(max=200)])
    title_en = StringField("Title (EN)", validators=[DataRequired(), Length(max=250)])
    title_ar = StringField("Title (AR)", validators=[DataRequired(), Length(max=250)])
    summary_en = TextAreaField("Summary (EN)", validators=[Optional()])
    summary_ar = TextAreaField("Summary (AR)", validators=[Optional()])
    body_en = TextAreaField("Body (EN)", validators=[DataRequired()])
    body_ar = TextAreaField("Body (AR)", validators=[DataRequired()])
    image_path = StringField("Image path", validators=[Optional(), Length(max=500)])
    category = StringField("Category", validators=[Optional(), Length(max=80)])
    is_published = BooleanField("Published", default=False)
    sort_order = IntegerField("Sort order", default=0)
    submit = SubmitField("Save article")


class ChallengeForm(FlaskForm):
    key = StringField("Key", validators=[DataRequired(), Length(max=100)])
    title_en = StringField("Title (EN)", validators=[DataRequired(), Length(max=200)])
    title_ar = StringField("Title (AR)", validators=[DataRequired(), Length(max=200)])
    description_en = TextAreaField("Description (EN)", validators=[DataRequired()])
    description_ar = TextAreaField("Description (AR)", validators=[DataRequired()])
    type = SelectField(
        "Type",
        choices=[("weekly", "Weekly"), ("monthly", "Monthly"), ("community", "Community")],
        validators=[DataRequired()],
    )
    category_id = SelectField("Category", coerce=int, validators=[Optional()])
    target_type = SelectField(
        "Target type",
        choices=[
            ("record_count", "Record count"),
            ("reduction_percent", "Reduction percent"),
            ("action_count", "Completed actions"),
            ("streak", "Day streak"),
        ],
        validators=[DataRequired()],
    )
    target_value = IntegerField("Target value", validators=[DataRequired(), NumberRange(min=1)])
    points = IntegerField("Points", default=50, validators=[NumberRange(min=0)])
    badge_id = SelectField("Badge", coerce=int, validators=[Optional()])
    start_date = DateField("Start", validators=[DataRequired()])
    end_date = DateField("End", validators=[DataRequired()])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save challenge")


class BadgeForm(FlaskForm):
    key = StringField("Key", validators=[DataRequired(), Length(max=80)])
    title_en = StringField("Title (EN)", validators=[DataRequired(), Length(max=160)])
    title_ar = StringField("Title (AR)", validators=[DataRequired(), Length(max=160)])
    description_en = TextAreaField("Description (EN)", validators=[DataRequired()])
    description_ar = TextAreaField("Description (AR)", validators=[DataRequired()])
    icon = StringField("Icon key", validators=[Optional(), Length(max=60)])
    criteria = TextAreaField("Criteria", validators=[DataRequired()])
    points = IntegerField("Points", default=0, validators=[NumberRange(min=0)])
    submit = SubmitField("Save badge")


class NotificationForm(FlaskForm):
    target = SelectField(
        "Target",
        choices=[("all", "All active users"), ("email", "One user by email")],
        validators=[DataRequired()],
    )
    email = StringField("User email", validators=[Optional(), Email(), Length(max=255)])
    type = SelectField(
        "Type",
        choices=[
            ("announcement", "Announcement"),
            ("reminder", "Reminder"),
            ("goal", "Goal"),
            ("alert", "Alert"),
            ("plan", "Plan"),
            ("challenge", "Challenge"),
            ("summary", "Summary"),
        ],
        validators=[DataRequired()],
    )
    title_en = StringField("Title (EN)", validators=[DataRequired(), Length(max=200)])
    title_ar = StringField("Title (AR)", validators=[DataRequired(), Length(max=200)])
    body_en = TextAreaField("Body (EN)", validators=[DataRequired()])
    body_ar = TextAreaField("Body (AR)", validators=[DataRequired()])
    action_url = StringField("Action URL", validators=[Optional(), Length(max=300)])
    submit = SubmitField("Send notification")


class SettingsForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=200)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("New password (optional)", validators=[Optional(), Length(min=8)])
    submit = SubmitField("Save profile")


class AdminForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=200)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    role = SelectField(
        "Role",
        choices=[("content_editor", "Content editor"), ("super_admin", "Super admin")],
        validators=[DataRequired()],
    )
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    submit = SubmitField("Create admin")


class AppSettingForm(FlaskForm):
    key = StringField("Key", validators=[DataRequired(), Length(max=120)])
    value = TextAreaField("Value", validators=[DataRequired()])
    submit = SubmitField("Save setting")


class FlagResolveForm(FlaskForm):
    status = SelectField(
        "Status",
        choices=[("reviewed", "Reviewed"), ("dismissed", "Dismissed")],
        validators=[DataRequired()],
    )
    admin_notes = TextAreaField("Notes", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Resolve")
