"""Import every model so SQLAlchemy metadata and Alembic see all tables."""

from app.modules.admin.models import Admin, AdminAuditLog, AppSetting
from app.modules.ai.models import (
    AiCache,
    AiConversation,
    AiFlaggedResponse,
    AiMessage,
    AiUsage,
)
from app.modules.alternatives.models import Alternative, SavedAlternative
from app.modules.catalog.models import EmissionCategory, EmissionFactor
from app.modules.challenges.models import (
    Badge,
    Challenge,
    ChallengeParticipant,
    PointsLedger,
    UserBadge,
)
from app.modules.content.models import Article
from app.modules.documents.models import Document
from app.modules.goals.models import Goal
from app.modules.notifications.models import Notification, NotificationPreference
from app.modules.organizations.models import Organization
from app.modules.plans.models import PlanAction, ReductionPlan
from app.modules.records.models import ConsumptionRecord
from app.modules.users.models import RefreshToken, User, UserProfile

__all__ = [
    "Admin",
    "AdminAuditLog",
    "AiCache",
    "AiConversation",
    "AiFlaggedResponse",
    "AiMessage",
    "AiUsage",
    "Alternative",
    "AppSetting",
    "Article",
    "Badge",
    "Challenge",
    "ChallengeParticipant",
    "ConsumptionRecord",
    "Document",
    "EmissionCategory",
    "EmissionFactor",
    "Goal",
    "Notification",
    "NotificationPreference",
    "Organization",
    "PlanAction",
    "PointsLedger",
    "ReductionPlan",
    "RefreshToken",
    "SavedAlternative",
    "User",
    "UserBadge",
    "UserProfile",
]
