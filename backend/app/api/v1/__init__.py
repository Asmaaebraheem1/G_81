"""API v1 package: register every route module on the blueprint."""

# Import order is intentional: each module attaches routes to api_v1.
from app.api.v1 import (  # noqa: E402,F401
    ai,
    alternatives,
    auth,
    catalog,
    challenges,
    documents,
    goals,
    notifications,
    plans,
    records,
    reports,
)
from app.api.v1.blueprint import api_v1

__all__ = ["api_v1"]
