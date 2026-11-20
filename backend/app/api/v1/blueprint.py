"""API v1 blueprint and tags."""

from __future__ import annotations

from flask_openapi3 import APIBlueprint, Tag

TAG_HEALTH = Tag(name="Health", description="Service status")
TAG_AUTH = Tag(name="Auth", description="Registration, login, tokens, profile")
TAG_CATALOG = Tag(name="Catalog", description="Categories and documented emission factors")
TAG_RECORDS = Tag(name="Records", description="Consumption records and calculations")
TAG_DOCUMENTS = Tag(name="Documents", description="Private bill/receipt uploads and extraction")
TAG_REPORTS = Tag(name="Reports", description="Dashboard, reports, trend, and export")
TAG_GOALS = Tag(name="Goals", description="Reduction goals")
TAG_PLANS = Tag(name="Plans", description="AI-assisted reduction plans")
TAG_ALTERNATIVES = Tag(name="Alternatives", description="Curated sustainable alternatives")
TAG_CHALLENGES = Tag(name="Challenges", description="Challenges, achievements, leaderboard")
TAG_NOTIFICATIONS = Tag(name="Notifications", description="In-app notifications and preferences")
TAG_AI = Tag(name="AI", description="Assistant, insights, summary, and flags")
TAG_CONTENT = Tag(name="Content", description="Educational articles")

api_v1 = APIBlueprint(
    "api_v1",
    __name__,
    url_prefix="/api/v1",
    abp_tags=[
        TAG_HEALTH,
        TAG_AUTH,
        TAG_CATALOG,
        TAG_RECORDS,
        TAG_DOCUMENTS,
        TAG_REPORTS,
        TAG_GOALS,
        TAG_PLANS,
        TAG_ALTERNATIVES,
        TAG_CHALLENGES,
        TAG_NOTIFICATIONS,
        TAG_AI,
        TAG_CONTENT,
    ],
)
