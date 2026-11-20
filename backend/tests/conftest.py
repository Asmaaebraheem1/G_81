"""Shared pytest fixtures: isolated in-memory database with a small catalog."""

from __future__ import annotations

from datetime import date

import pytest

from app import create_app
from app.core.config import TestingConfig
from app.core.db import db, utcnow
from app.core.security import hash_password
from app.modules.admin.models import Admin
from app.modules.alternatives.models import Alternative
from app.modules.catalog.models import EmissionCategory, EmissionFactor
from app.modules.challenges.models import Badge, Challenge
from app.modules.content.models import Article
from app.modules.notifications.models import Notification
from app.modules.organizations.models import Organization
from app.modules.users.models import User, UserProfile

USER_EMAIL = "sara@example.com"
USER_PASSWORD = "User123!"
OTHER_EMAIL = "ahmad@example.com"
ORG_EMAIL = "org@example.com"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "Admin123!"
EDITOR_EMAIL = "editor@example.com"
EDITOR_PASSWORD = "Editor123!"
DEMO_TODAY = date(2026, 6, 30)


def _seed(app) -> dict:
    electricity = EmissionCategory(
        key="electricity",
        name_en="Electricity",
        name_ar="الكهرباء",
        description_en="Grid electricity.",
        description_ar="كهرباء الشبكة.",
        icon="bolt",
        color_hex="#d8a33a",
        unit_hint="kWh",
        sort_order=0,
        is_active=True,
    )
    transport = EmissionCategory(
        key="transport",
        name_en="Transport",
        name_ar="النقل",
        unit_hint="km",
        sort_order=1,
        is_active=True,
    )
    food = EmissionCategory(
        key="food",
        name_en="Food",
        name_ar="الطعام",
        unit_hint="kg",
        sort_order=2,
        is_active=True,
    )
    waste = EmissionCategory(
        key="waste",
        name_en="Waste",
        name_ar="النفايات",
        unit_hint="kg",
        sort_order=3,
        is_active=True,
    )
    db.session.add_all([electricity, transport, food, waste])
    db.session.flush()

    grid = EmissionFactor(
        category_id=electricity.id,
        key="grid_electricity",
        name_en="Grid electricity",
        name_ar="كهرباء الشبكة",
        activity_type="grid_electricity",
        unit="kWh",
        factor_grams_co2e=233,
        source_name="DEFRA/BEIS",
        source_year=2025,
        region="UK",
        valid_from=date(2024, 1, 1),
        is_active=True,
    )
    car = EmissionFactor(
        category_id=transport.id,
        key="petrol_car",
        name_en="Petrol car",
        name_ar="سيارة بنزين",
        activity_type="petrol_car",
        unit="km",
        factor_grams_co2e=170,
        source_name="DEFRA/BEIS",
        source_year=2025,
        region="UK",
        valid_from=date(2024, 1, 1),
        is_active=True,
    )
    beef = EmissionFactor(
        category_id=food.id,
        key="beef",
        name_en="Beef",
        name_ar="لحم البقر",
        activity_type="beef",
        unit="kg",
        factor_grams_co2e=60000,
        source_name="Poore & Nemecek",
        source_year=2018,
        region="GLOBAL",
        valid_from=date(2020, 1, 1),
        is_active=True,
    )
    landfill = EmissionFactor(
        category_id=waste.id,
        key="landfill_waste",
        name_en="Landfill waste",
        name_ar="نفايات المكب",
        activity_type="landfill_waste",
        unit="kg",
        factor_grams_co2e=586,
        source_name="DEFRA/BEIS",
        source_year=2025,
        region="UK",
        valid_from=date(2024, 1, 1),
        is_active=True,
    )
    db.session.add_all([grid, car, beef, landfill])
    db.session.flush()

    user = User(
        email=USER_EMAIL,
        password_hash=hash_password(USER_PASSWORD),
        full_name="Sara Ahmed",
        account_type="individual",
        locale="en",
        timezone="UTC",
        is_active=True,
    )
    other = User(
        email=OTHER_EMAIL,
        password_hash=hash_password(USER_PASSWORD),
        full_name="Ahmad Ali",
        account_type="individual",
        locale="ar",
    )
    org = Organization(
        name_en="Green Demo Org",
        name_ar="منظمة تجريبية",
        slug="green-demo-org",
        org_type="business",
        contact_email=ORG_EMAIL,
        is_active=True,
    )
    db.session.add_all([user, other, org])
    db.session.flush()
    org_user = User(
        email=ORG_EMAIL,
        password_hash=hash_password(USER_PASSWORD),
        full_name="Org Owner",
        account_type="organization",
        organization_id=org.id,
        is_org_owner=True,
        locale="en",
    )
    db.session.add(org_user)
    db.session.flush()
    db.session.add_all(
        [
            UserProfile(user_id=user.id, household_size=3, onboarding_completed=True),
            UserProfile(user_id=other.id, onboarding_completed=True),
            UserProfile(user_id=org_user.id, onboarding_completed=True),
            Alternative(
                key="led-lighting",
                title_en="Switch to LED lighting",
                title_ar="التحول إلى إضاءة LED",
                description_en="Replace old bulbs.",
                description_ar="استبدل المصابيح القديمة.",
                assumption_en="An 8% reduction in electricity use.",
                assumption_ar="خفض 8% من استهلاك الكهرباء.",
                category_id=electricity.id,
                estimated_reduction_percent=8,
                source_name="CarbonWise catalog",
                icon="bolt",
                is_active=True,
                sort_order=0,
            ),
            Alternative(
                key="public-transport",
                title_en="Use public transport",
                title_ar="استخدم النقل العام",
                description_en="Replace car trips.",
                description_ar="استبدل رحلات السيارة.",
                assumption_en="A 15% reduction in road transport.",
                assumption_ar="خفض 15% من النقل البري.",
                category_id=transport.id,
                estimated_reduction_percent=15,
                is_active=True,
                sort_order=1,
            ),
            Article(
                slug="how-to-start",
                title_en="How to start",
                title_ar="كيف تبدأ",
                summary_en="A practical first step.",
                summary_ar="خطوة أولى عملية.",
                body_en="Start with one measured change.",
                body_ar="ابدأ بتغيير واحد قابل للقياس.",
                category="guide",
                is_published=True,
            ),
            Badge(
                key="first-record",
                title_en="First record",
                title_ar="أول سجل",
                description_en="Added the first record.",
                description_ar="أضفت أول سجل.",
                icon="star",
                criteria="Add one record",
                points=10,
            ),
        ]
    )
    badge = Badge.query.filter_by(key="first-record").first()
    db.session.add(
        Challenge(
            key="record-two",
            title_en="Record two activities",
            title_ar="سجل نشاطين",
            description_en="Log two activities this week.",
            description_ar="سجل نشاطين هذا الأسبوع.",
            type="weekly",
            target_type="record_count",
            target_value=2,
            points=20,
            badge_id=badge.id if badge else None,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 7, 31),
            is_active=True,
        )
    )
    db.session.add(
        Notification(
            user_id=user.id,
            type="announcement",
            title_en="Welcome",
            title_ar="مرحبًا",
            body_en="Your demo is ready.",
            body_ar="عرضك التجريبي جاهز.",
            created_at=utcnow(),
        )
    )
    admin = Admin(
        email=ADMIN_EMAIL,
        password_hash=hash_password(ADMIN_PASSWORD),
        name="Demo Admin",
        role="super_admin",
        is_active=True,
    )
    editor = Admin(
        email=EDITOR_EMAIL,
        password_hash=hash_password(EDITOR_PASSWORD),
        name="Demo Editor",
        role="content_editor",
        is_active=True,
    )
    db.session.add_all([admin, editor])
    db.session.commit()

    return {
        "user": user,
        "other": other,
        "org_user": org_user,
        "grid": grid,
        "car": car,
        "beef": beef,
        "landfill": landfill,
        "electricity": electricity,
        "transport": transport,
        "food": food,
        "waste": waste,
        "challenge": Challenge.query.filter_by(key="record-two").first(),
        "alternative": Alternative.query.filter_by(key="led-lighting").first(),
        "article": Article.query.filter_by(slug="how-to-start").first(),
    }


@pytest.fixture()
def app(tmp_path):
    application = create_app(TestingConfig)
    application.config.update(
        DEMO_TODAY=DEMO_TODAY,
        DEMO_SEED_DATE=DEMO_TODAY,
        UPLOAD_FOLDER=str(tmp_path / "uploads"),
        AI_SCREENSHOT_MODE=False,
        OPENROUTER_API_KEY="",
        WTF_CSRF_ENABLED=False,
    )
    with application.app_context():
        db.create_all()
        application.seed_data = _seed(application)  # type: ignore[attr-defined]
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def data(app):
    return app.seed_data  # type: ignore[attr-defined]


@pytest.fixture()
def accounts():
    return {
        "user": (USER_EMAIL, USER_PASSWORD),
        "other": (OTHER_EMAIL, USER_PASSWORD),
        "org": (ORG_EMAIL, USER_PASSWORD),
        "admin": (ADMIN_EMAIL, ADMIN_PASSWORD),
        "editor": (EDITOR_EMAIL, EDITOR_PASSWORD),
    }
