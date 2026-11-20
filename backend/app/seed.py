"""Deterministic six-month demo seed.

Run with:  flask seed --reset
The window ends on DEMO_SEED_DATE (default 2026-06-30). No real personal data.
"""

from __future__ import annotations

import hashlib
import json
import random
from datetime import date, datetime, time, timedelta
from pathlib import Path

from flask import current_app
from PIL import Image, ImageDraw

from app.core.db import db, utcnow
from app.core.emissions import calculate_emissions_grams, factor_source_text
from app.core.security import hash_password
from app.core.text import slugify
from app.modules.admin.models import Admin, AdminAuditLog, AppSetting
from app.modules.ai.models import AiConversation, AiMessage, AiUsage
from app.modules.alternatives.models import Alternative
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
from app.modules.users.models import User, UserProfile

RNG = random.Random(42)


def seed_database(reset: bool = False) -> None:
    if reset:
        db.drop_all()
        db.create_all()
    else:
        db.create_all()
        if Admin.query.first() is not None:
            return

    categories = _seed_categories()
    factors = _seed_factors(categories)
    _seed_alternatives(categories)
    admins = _seed_admins()
    users, org = _seed_users()
    records = _seed_records(users, categories, factors)
    _seed_documents(users, records)
    goals = _seed_goals(users, org)
    _seed_plans(users, org, goals, categories)
    badges = _seed_badges()
    challenges = _seed_challenges(categories, badges)
    _seed_participation(users, challenges, badges)
    _seed_points(users, challenges)
    _seed_notifications(users)
    _seed_articles()
    _seed_ai(users)
    _seed_audit(admins)
    _seed_settings()
    db.session.commit()


def _seed_categories() -> dict[str, EmissionCategory]:
    data = [
        ("electricity", "Electricity", "الكهرباء", "kWh", "#d8a33a", "bolt"),
        ("transport", "Transport", "النقل", "km", "#2f8f6b", "car"),
        ("flights", "Flights", "الطيران", "passenger_km", "#5b7cfa", "plane"),
        ("water", "Water", "المياه", "m³", "#3aa6c9", "drop"),
        ("waste", "Waste", "النفايات", "kg", "#8a6f4d", "trash"),
        ("food", "Food", "الطعام", "kg", "#c25a3a", "bowl"),
        ("shopping", "Shopping", "الشراء", "item", "#7a5aa8", "bag"),
    ]
    result = {}
    for index, (key, en, ar, unit, color, icon) in enumerate(data):
        row = EmissionCategory(
            key=key,
            name_en=en,
            name_ar=ar,
            description_en=f"Activities related to {en.lower()}.",
            description_ar=f"الأنشطة المتعلقة بـ{ar}.",
            icon=icon,
            color_hex=color,
            unit_hint=unit,
            sort_order=index,
            is_active=True,
        )
        db.session.add(row)
        result[key] = row
    db.session.flush()
    return result


def _seed_factors(categories: dict[str, EmissionCategory]) -> dict[str, EmissionFactor]:
    data = [
        (
            "grid_electricity",
            "electricity",
            "Grid electricity",
            "كهرباء الشبكة",
            "grid_electricity",
            "kWh",
            233,
            "DEFRA/BEIS",
            2025,
            "UK",
            "Average UK grid intensity; demo default.",
        ),
        (
            "natural_gas",
            "electricity",
            "Natural gas",
            "الغاز الطبيعي",
            "natural_gas",
            "m³",
            2020,
            "DEFRA/BEIS",
            2025,
            "UK",
            "Gross calorific value basis.",
        ),
        (
            "petrol_car",
            "transport",
            "Petrol car",
            "سيارة بنزين",
            "petrol_car",
            "km",
            170,
            "DEFRA/BEIS",
            2025,
            "UK",
            "Average passenger car.",
        ),
        (
            "diesel_car",
            "transport",
            "Diesel car",
            "سيارة ديزل",
            "diesel_car",
            "km",
            171,
            "DEFRA/BEIS",
            2025,
            "UK",
            "Average passenger car.",
        ),
        (
            "hybrid_car",
            "transport",
            "Hybrid car",
            "سيارة هجينة",
            "hybrid_car",
            "km",
            90,
            "DEFRA/BEIS",
            2025,
            "UK",
            "Plug-in hybrid average.",
        ),
        (
            "bus",
            "transport",
            "Bus",
            "الحافلة",
            "bus",
            "passenger_km",
            82,
            "DEFRA/BEIS",
            2025,
            "UK",
            "Local bus average.",
        ),
        (
            "train",
            "transport",
            "Rail",
            "القطار",
            "train",
            "passenger_km",
            35,
            "DEFRA/BEIS",
            2025,
            "UK",
            "National rail average.",
        ),
        (
            "flight_short",
            "flights",
            "Short-haul flight",
            "رحلة قصيرة",
            "flight_short",
            "passenger_km",
            255,
            "DEFRA/BEIS",
            2025,
            "GLOBAL",
            "Economy, short-haul.",
        ),
        (
            "flight_long",
            "flights",
            "Long-haul flight",
            "رحلة طويلة",
            "flight_long",
            "passenger_km",
            150,
            "DEFRA/BEIS",
            2025,
            "GLOBAL",
            "Economy, long-haul.",
        ),
        (
            "water_supply",
            "water",
            "Water supply",
            "إمداد المياه",
            "water_supply",
            "m³",
            344,
            "UK Water Industry",
            2024,
            "UK",
            "Supply and treatment.",
        ),
        (
            "wastewater",
            "water",
            "Wastewater",
            "مياه الصرف",
            "wastewater",
            "m³",
            272,
            "UK Water Industry",
            2024,
            "UK",
            "Treatment estimate.",
        ),
        (
            "landfill_waste",
            "waste",
            "Landfill waste",
            "نفايات المكب",
            "landfill_waste",
            "kg",
            586,
            "DEFRA/BEIS",
            2025,
            "UK",
            "Mixed household waste.",
        ),
        (
            "recycled_waste",
            "waste",
            "Recycled waste",
            "نفايات معاد تدويرها",
            "recycled_waste",
            "kg",
            21,
            "DEFRA/BEIS",
            2025,
            "UK",
            "Collection and reprocessing.",
        ),
        (
            "beef",
            "food",
            "Beef",
            "لحم البقر",
            "beef",
            "kg",
            60000,
            "Poore & Nemecek / Our World in Data",
            2018,
            "GLOBAL",
            "High-impact food; illustrative.",
        ),
        (
            "chicken",
            "food",
            "Chicken",
            "الدجاج",
            "chicken",
            "kg",
            6900,
            "Poore & Nemecek / Our World in Data",
            2018,
            "GLOBAL",
            "Illustrative.",
        ),
        (
            "vegetables",
            "food",
            "Vegetables",
            "الخضروات",
            "vegetables",
            "kg",
            2000,
            "Poore & Nemecek / Our World in Data",
            2018,
            "GLOBAL",
            "Illustrative.",
        ),
        (
            "dairy",
            "food",
            "Dairy",
            "منتجات الألبان",
            "dairy",
            "kg",
            3200,
            "Poore & Nemecek / Our World in Data",
            2018,
            "GLOBAL",
            "Illustrative.",
        ),
        (
            "clothing",
            "shopping",
            "Clothing",
            "الملابس",
            "clothing",
            "item",
            15000,
            "WRAP / DEFRA",
            2024,
            "UK",
            "Average garment; illustrative.",
        ),
        (
            "electronics",
            "shopping",
            "Electronics",
            "الإلكترونيات",
            "electronics",
            "item",
            50000,
            "Manufacturer LCA range",
            2024,
            "GLOBAL",
            "Small device; illustrative.",
        ),
        (
            "delivery",
            "shopping",
            "Delivery parcel",
            "طرد توصيل",
            "delivery",
            "package",
            500,
            "DEFRA/BEIS",
            2025,
            "UK",
            "Last-mile van delivery.",
        ),
    ]
    result = {}
    for key, cat, en, ar, activity, unit, grams, source, year, region, notes in data:
        row = EmissionFactor(
            category_id=categories[cat].id,
            key=key,
            name_en=en,
            name_ar=ar,
            activity_type=activity,
            unit=unit,
            factor_grams_co2e=grams,
            source_name=source,
            source_url=(
                "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2025"
                if "DEFRA" in source
                else None
            ),
            source_year=year,
            region=region,
            valid_from=date(2024, 1, 1),
            is_active=True,
            notes=notes,
        )
        db.session.add(row)
        result[key] = row
    db.session.flush()
    return result


def _seed_alternatives(categories: dict[str, EmissionCategory]) -> list[Alternative]:
    data = [
        (
            "led-lighting",
            "Switch to LED lighting",
            "التحول إلى إضاءة LED",
            "electricity",
            8,
            "Replacing remaining bulbs with LEDs; assumption is 8% of current electricity use.",
            "استبدال المصابيح المتبقية بمصابيح LED؛ الافتراض خفض 8% من استهلاك الكهرباء الحالي.",
        ),
        (
            "smart-thermostat",
            "Install a smart thermostat",
            "ترك منظم حرارة ذكي",
            "electricity",
            6,
            "Better scheduling and setpoints; assumption is 6% of heating/cooling energy.",
            "جدولة أفضل وضبط للحرارة؛ الافتراض خفض 6% من طاقة التدفئة والتبريد.",
        ),
        (
            "renewable-tariff",
            "Choose a renewable tariff",
            "اختيار تعرفة طاقة متجددة",
            "electricity",
            20,
            "Supplier-backed renewable electricity; grid-factor assumption is illustrative.",
            "كهرباء متجددة مدعومة من المورد؛ افتراض عامل الشبكة توضيحي.",
        ),
        (
            "public-transport",
            "Use public transport twice a week",
            "استخدام النقل العام مرتين أسبوعيًا",
            "transport",
            15,
            "Replace two routine car trips; 15% of road transport.",
            "استبدال رحلتين معتادتين بالسيارة؛ 15% من النقل البري.",
        ),
        (
            "carpool",
            "Carpool one day a week",
            "مشاركة السيارة يومًا أسبوعيًا",
            "transport",
            9,
            "One shared commute day; 9% of road transport.",
            "يوم واحد للمشاركة في التنقل؛ 9% من النقل البري.",
        ),
        (
            "ev-switch",
            "Switch to an electric vehicle",
            "التحول إلى سيارة كهربائية",
            "transport",
            25,
            "Tailpipe-free driving, grid charging; 25% of road transport.",
            "قيادة بدون عادم مع شحن من الشبكة؛ 25% من النقل البري.",
        ),
        (
            "rail-short-haul",
            "Take rail for short trips",
            "استخدام القطار للرحلات القصيرة",
            "flights",
            12,
            "Replace one short-haul flight; 12% of flight emissions.",
            "استبدال رحلة قصيرة واحدة؛ 12% من انبعاثات الطيران.",
        ),
        (
            "video-meetings",
            "Replace a trip with video",
            "استبدال رحلة باجتماع فيديو",
            "flights",
            5,
            "One avoided business trip; 5% of flight emissions.",
            "رحلة عمل يتم تجنبها؛ 5% من انبعاثات الطيران.",
        ),
        (
            "plant-based",
            "Add three plant-based meals",
            "إضافة ثلاث وجبات نباتية",
            "food",
            10,
            "Three meals per week; 10% of food emissions.",
            "ثلاث وجبات أسبوعيًا؛ 10% من انبعاثات الطعام.",
        ),
        (
            "food-waste",
            "Plan meals to cut food waste",
            "تخطيط الوجبات لتقليل الهدر",
            "waste",
            20,
            "Meal planning and portion control; 20% of food-waste emissions.",
            "تخطيط الوجبات والتحكم بالحصص؛ 20% من انبعاثات هدر الطعام.",
        ),
        (
            "repair-clothing",
            "Repair or buy second-hand",
            "الإصلاح أو الشراء المستعمل",
            "shopping",
            5,
            "One repaired/second-hand purchase; 5% of shopping emissions.",
            "شراء واحد مصلح أو مستعمل؛ 5% من انبعاثات الشراء.",
        ),
        (
            "recycle-more",
            "Separate recycling at home",
            "فصل إعادة التدوير في المنزل",
            "waste",
            18,
            "Better separation; 18% of household waste emissions.",
            "فصل أفضل؛ 18% من انبعاثات النفايات المنزلية.",
        ),
    ]
    rows = []
    for index, (key, en, ar, cat, pct, assumption_en, assumption_ar) in enumerate(data):
        row = Alternative(
            key=key,
            title_en=en,
            title_ar=ar,
            description_en=f"A practical option to reduce {cat} emissions. " + assumption_en,
            description_ar=f"خيار عملي لخفض انبعاثات {ar}. " + assumption_ar,
            category_id=categories[cat].id,
            estimated_reduction_percent=pct,
            assumption_en=assumption_en,
            assumption_ar=assumption_ar,
            source_name="CarbonWise curated assumption",
            icon=cat,
            is_active=True,
            sort_order=index,
        )
        db.session.add(row)
        rows.append(row)
    db.session.flush()
    return rows


def _seed_admins() -> list[Admin]:
    rows = [
        Admin(
            email="admin@carbonwise.demo",
            password_hash=hash_password("Admin123!"),
            name="Maya Admin",
            role="super_admin",
            is_active=True,
        ),
        Admin(
            email="editor@carbonwise.demo",
            password_hash=hash_password("Editor123!"),
            name="Omar Editor",
            role="content_editor",
            is_active=True,
        ),
    ]
    db.session.add_all(rows)
    db.session.flush()
    return rows


def _seed_users() -> tuple[dict[str, User], Organization]:
    org = Organization(
        name_en="Green Horizon Trading",
        name_ar="الأفق الأخضر للتجارة",
        slug="green-horizon-trading",
        org_type="business",
        industry="Retail",
        country="United Arab Emirates",
        city="Dubai",
        size="11-50",
        contact_email="org@carbonwise.demo",
        is_verified=True,
        is_active=True,
    )
    db.session.add(org)
    db.session.flush()

    sara = User(
        email="sara@carbonwise.demo",
        password_hash=hash_password("User123!"),
        full_name="Sara Al Mansoori",
        account_type="individual",
        locale="en",
        timezone="Asia/Dubai",
        is_active=True,
    )
    ahmad = User(
        email="ahmad@carbonwise.demo",
        password_hash=hash_password("User123!"),
        full_name="Ahmad Khalid",
        account_type="household",
        locale="ar",
        timezone="Asia/Riyadh",
        is_active=True,
    )
    org_user = User(
        email="org@carbonwise.demo",
        password_hash=hash_password("Org123!"),
        full_name="Layla Hassan",
        account_type="organization",
        organization_id=org.id,
        is_org_owner=True,
        locale="en",
        timezone="Asia/Dubai",
        is_active=True,
    )
    db.session.add_all([sara, ahmad, org_user])
    db.session.flush()

    profiles = [
        UserProfile(
            user_id=sara.id,
            country="United Arab Emirates",
            city="Dubai",
            household_size=3,
            home_type="apartment",
            leaderboard_opt_in=True,
            leaderboard_alias="Sara G.",
            onboarding_completed=True,
            default_period="month",
        ),
        UserProfile(
            user_id=ahmad.id,
            country="Saudi Arabia",
            city="Riyadh",
            household_size=5,
            home_type="house",
            leaderboard_opt_in=True,
            leaderboard_alias="أحمد",
            onboarding_completed=True,
            default_period="month",
        ),
        UserProfile(
            user_id=org_user.id,
            country="United Arab Emirates",
            city="Dubai",
            leaderboard_opt_in=False,
            onboarding_completed=True,
            default_period="month",
        ),
    ]
    db.session.add_all(profiles)
    for user in (sara, ahmad):
        for type_name in [
            "reminder",
            "goal",
            "alert",
            "plan",
            "challenge",
            "summary",
            "announcement",
        ]:
            db.session.add(NotificationPreference(user_id=user.id, type=type_name, enabled=True))
    db.session.flush()
    return {"sara": sara, "ahmad": ahmad, "org": org_user}, org


def _record(
    user: User,
    category: EmissionCategory,
    factor: EmissionFactor,
    activity_date: date,
    quantity: float,
    notes: str | None = None,
    source: str = "seed",
) -> ConsumptionRecord:
    grams = calculate_emissions_grams(quantity, factor.factor_grams_co2e)
    row = ConsumptionRecord(
        user_id=user.id,
        organization_id=user.organization_id if user.account_type == "organization" else None,
        category_id=category.id,
        factor_id=factor.id,
        activity_date=activity_date,
        quantity=quantity,
        unit=factor.unit,
        factor_grams_co2e_snapshot=factor.factor_grams_co2e,
        factor_source_snapshot=factor_source_text(factor),
        emissions_grams=grams,
        notes=notes,
        status="active",
        source=source,
    )
    db.session.add(row)
    return row


def _seed_records(
    users: dict[str, User],
    categories: dict[str, EmissionCategory],
    factors: dict[str, EmissionFactor],
) -> list[ConsumptionRecord]:
    end = current_app.config.get("DEMO_SEED_DATE", date(2026, 6, 30))
    if isinstance(end, str):
        end = date.fromisoformat(end)
    rows: list[ConsumptionRecord] = []
    plans = [
        ("sara", 6, 1.0),
        ("sara", 5, 0.7),
        ("ahmad", 4, 1.1),
        ("org", 3, 1.4),
    ]
    for user_key, per_month, factor_scale in plans:
        user = users[user_key]
        for month_offset in range(6):
            year = end.year
            month = end.month - month_offset
            while month <= 0:
                month += 12
                year -= 1
            picks = [
                (
                    "grid_electricity",
                    "electricity",
                    RNG.uniform(80, 210) * factor_scale,
                    "Monthly electricity",
                ),
                ("petrol_car", "transport", RNG.uniform(60, 260) * factor_scale, "Commuting"),
                ("vegetables", "food", RNG.uniform(1.0, 4.5), "Groceries"),
                ("water_supply", "water", RNG.uniform(4, 16), "Water bill"),
                ("landfill_waste", "waste", RNG.uniform(2, 9), "Household waste"),
                ("delivery", "shopping", RNG.randint(1, 4), "Online order"),
                ("bus", "transport", RNG.uniform(20, 110), "Bus trips"),
                ("chicken", "food", RNG.uniform(0.5, 2.0), "Groceries"),
                ("natural_gas", "electricity", RNG.uniform(8, 35), "Gas bill"),
                ("recycled_waste", "waste", RNG.uniform(2, 12), "Recycling"),
            ]
            if month_offset in {0, 2, 4}:
                picks.append(("flight_short", "flights", RNG.uniform(700, 1900), "Short trip"))
            if user_key == "org":
                picks.append(("electronics", "shopping", 1, "Office equipment"))
            for index, (factor_key, category_key, quantity, note) in enumerate(picks[:per_month]):
                day = 3 + (index * 3 + month_offset) % 24
                rows.append(
                    _record(
                        user,
                        categories[category_key],
                        factors[factor_key],
                        date(year, month, day),
                        round(quantity, 2),
                        note,
                    )
                )
    db.session.flush()
    return rows


def _seed_documents(users: dict[str, User], records: list[ConsumptionRecord]) -> None:
    root = Path(current_app.config["UPLOAD_FOLDER"])
    root.mkdir(parents=True, exist_ok=True)
    linked = next(
        (
            row
            for row in records
            if row.user_id == users["sara"].id and row.factor.key == "grid_electricity"
        ),
        records[0] if records else None,
    )
    for index, (user_key, original, status, link) in enumerate(
        [
            ("sara", "city-electric-may-2026.png", "confirmed", True),
            ("sara", "water-bill-june-2026.png", "extracted", False),
            ("ahmad", "fuel-receipt-june-2026.png", "uploaded", False),
        ]
    ):
        user = users[user_key]
        folder = root / str(user.id)
        folder.mkdir(parents=True, exist_ok=True)
        filename = f"seed-{index + 1}-{slugify(original)}"
        path = folder / filename
        _draw_bill(path, original, index)
        data = {
            "vendor": (
                "City Electric"
                if index == 0
                else ("Water Authority" if index == 1 else "Fuel Station")
            ),
            "billing_period": "2026-05" if index == 0 else "2026-06",
            "consumption_value": 120.5 if index == 0 else (9.4 if index == 1 else 42.0),
            "unit": "kWh" if index == 0 else ("m³" if index == 1 else "L"),
            "confidence": 0.91 if index == 0 else 0.79,
        }
        document = Document(
            user_id=user.id,
            organization_id=user.organization_id if user.account_type == "organization" else None,
            original_filename=original,
            stored_filename=filename,
            mime_type="image/png",
            size_bytes=path.stat().st_size,
            storage_path=f"{user.id}/{filename}",
            status=status,
            ai_consent=True,
            extraction_json=json.dumps(data),
            extraction_model="seed-demo",
            confirmed_at=utcnow() if status == "confirmed" else None,
        )
        db.session.add(document)
        db.session.flush()
        if link and linked is not None and linked.user_id == user.id:
            document.record_id = linked.id
            linked.document_id = document.id
    db.session.flush()


def _draw_bill(path: Path, title: str, index: int) -> None:
    image = Image.new("RGB", (900, 1200), "#fbfbf8")
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, 900, 150], fill="#0f3d2e")
    draw.text((50, 48), "CARBONWISE DEMO BILL", fill="#ffffff")
    draw.text((50, 86), title, fill="#b9ddcd")
    draw.text((50, 200), "City Electric", fill="#122019")
    draw.text((50, 230), "Invoice period: May 2026", fill="#60726a")
    draw.line([50, 270, 850, 270], fill="#dfe8e3")
    lines = [
        ("Consumption", "120.5 kWh"),
        ("Unit price", "0.28"),
        ("Billing period", "2026-05"),
        ("Document", f"DEMO-{index + 1:03d}"),
    ]
    y = 310
    for label, value in lines:
        draw.text((50, y), label, fill="#60726a")
        draw.text((500, y), value, fill="#122019")
        y += 55
    draw.rectangle([50, 700, 850, 900], outline="#dfe8e3", width=2)
    draw.text((72, 725), "This is a generated demo document.", fill="#60726a")
    draw.text((72, 760), "No real customer data is used.", fill="#60726a")
    draw.text((72, 820), "Confirm the values in the app before saving.", fill="#2f8f6b")
    image.save(path, "PNG")


def _baseline(user: User, start: date, end: date) -> int:
    value = (
        db.session.query(db.func.coalesce(db.func.sum(ConsumptionRecord.emissions_grams), 0))
        .filter(
            ConsumptionRecord.user_id == user.id,
            ConsumptionRecord.status == "active",
            ConsumptionRecord.activity_date.between(start, end),
        )
        .scalar()
    )
    return int(value or 0)


def _seed_goals(users: dict[str, User], org: Organization) -> list[Goal]:
    rows = []
    definitions = [
        (
            "sara",
            "Cut June emissions by 10%",
            10,
            "monthly",
            date(2026, 6, 1),
            date(2026, 6, 30),
            date(2026, 5, 1),
            date(2026, 5, 31),
        ),
        (
            "ahmad",
            "Yearly 15% reduction",
            15,
            "yearly",
            date(2026, 6, 1),
            date(2026, 12, 31),
            date(2026, 1, 1),
            date(2026, 5, 31),
        ),
        (
            "org",
            "Q2 office reduction",
            12,
            "monthly",
            date(2026, 4, 1),
            date(2026, 6, 30),
            date(2026, 1, 1),
            date(2026, 3, 31),
        ),
        (
            "sara",
            "Last week: 5% lighter",
            5,
            "weekly",
            date(2026, 6, 24),
            date(2026, 6, 30),
            date(2026, 6, 17),
            date(2026, 6, 23),
        ),
    ]
    for user_key, title, pct, period_type, start, end, bstart, bend in definitions:
        user = users[user_key]
        baseline = _baseline(user, bstart, bend)
        if baseline <= 0:
            baseline = 100000
        target = round(baseline * (1 - pct / 100))
        row = Goal(
            user_id=user.id,
            organization_id=user.organization_id if user.account_type == "organization" else None,
            title=title,
            target_percent=pct,
            period_type=period_type,
            start_date=start,
            end_date=end,
            baseline_start=bstart,
            baseline_end=bend,
            baseline_emissions_grams=baseline,
            target_emissions_grams=target,
            status="active",
        )
        db.session.add(row)
        rows.append(row)
    db.session.flush()
    return rows


def _seed_plans(
    users: dict[str, User],
    org: Organization,
    goals: list[Goal],
    categories: dict[str, EmissionCategory],
) -> list[ReductionPlan]:
    rows = []
    definitions = [
        (
            "sara",
            "A lighter June",
            "Four actions focused on the largest calculated categories. Savings are documented backend assumptions.",
            [
                ("Cut standby and lighting waste", "electricity", "high", 10),
                ("Replace two car trips per week", "transport", "high", 15),
                ("Add three plant-based meals", "food", "medium", 10),
                ("Separate food waste", "waste", "medium", 20),
            ],
            "active",
            2,
        ),
        (
            "ahmad",
            "Household quick wins",
            "A draft plan for the whole household. Start with the two highest-impact actions.",
            [
                ("Switch to LED lighting", "electricity", "high", 8),
                ("Plan meals to cut waste", "waste", "medium", 18),
                ("Use the bus twice a week", "transport", "medium", 12),
            ],
            "draft",
            0,
        ),
        (
            "org",
            "Office reduction sprint",
            "A workplace sprint across electricity, commuting, and procurement.",
            [
                ("Schedule equipment shutdown", "electricity", "high", 7),
                ("Carpool one day a week", "transport", "medium", 9),
                ("Repair before replacing devices", "shopping", "low", 5),
            ],
            "active",
            1,
        ),
    ]
    for user_key, title, summary, actions, status, completed in definitions:
        user = users[user_key]
        goal = next((g for g in goals if g.user_id == user.id), None)
        plan = ReductionPlan(
            user_id=user.id,
            organization_id=user.organization_id if user.account_type == "organization" else None,
            goal_id=goal.id if goal else None,
            title=title,
            summary=summary,
            locale="ar" if user_key == "ahmad" else "en",
            source="seed",
            model=None,
            status=status,
            generated_at=utcnow(),
        )
        db.session.add(plan)
        db.session.flush()
        for index, (action_title, category_key, priority, pct) in enumerate(actions):
            category = categories[category_key]
            category_total = (
                db.session.query(
                    db.func.coalesce(db.func.sum(ConsumptionRecord.emissions_grams), 0)
                )
                .filter(
                    ConsumptionRecord.user_id == user.id,
                    ConsumptionRecord.category_id == category.id,
                    ConsumptionRecord.status == "active",
                )
                .scalar()
                or 0
            )
            saving = round(int(category_total) * pct / 100)
            row = PlanAction(
                plan_id=plan.id,
                title=action_title,
                description="A small, repeatable action. Track it for one month.",
                category_id=category.id,
                priority=priority,
                timeframe="this_month",
                estimated_saving_grams=saving,
                saving_assumption=f"Backend assumption: {pct}% of the selected category's calculated emissions. Not an AI estimate.",
                status=(
                    "completed"
                    if index < completed
                    else ("in_progress" if index == completed else "pending")
                ),
                completed_at=utcnow() if index < completed else None,
                sort_order=index,
            )
            db.session.add(row)
        rows.append(plan)
    db.session.flush()
    return rows


def _seed_badges() -> dict[str, Badge]:
    data = [
        (
            "first_record",
            "First record",
            "أول سجل",
            "Log your first activity.",
            "سجل أول نشاط لك.",
            "spark",
            20,
        ),
        (
            "streak_7",
            "7-day streak",
            "سلسلة 7 أيام",
            "Record activity on seven consecutive days.",
            "سجل نشاطًا في سبعة أيام متتالية.",
            "flame",
            70,
        ),
        (
            "streak_30",
            "30-day streak",
            "سلسلة 30 يومًا",
            "Record activity on thirty consecutive days.",
            "سجل نشاطًا في ثلاثين يومًا متتالية.",
            "flame",
            200,
        ),
        (
            "goal_set",
            "Goal setter",
            "واضع هدف",
            "Create your first reduction goal.",
            "أنشئ أول هدف خفض لك.",
            "target",
            40,
        ),
        (
            "goal_achieved",
            "Goal achieved",
            "هدف محقق",
            "Complete a reduction goal.",
            "أكمل هدف خفض.",
            "trophy",
            150,
        ),
        (
            "plan_started",
            "Plan started",
            "خطة بدأت",
            "Generate or create a reduction plan.",
            "أنشئ خطة خفض.",
            "map",
            50,
        ),
        (
            "plan_completed",
            "Plan completed",
            "خطة مكتملة",
            "Complete every action in a plan.",
            "أكمل كل إجراءات خطة.",
            "check",
            180,
        ),
        (
            "challenge_joined",
            "Challenge joiner",
            "منضم للتحدي",
            "Join your first challenge.",
            "انضم إلى أول تحدٍ.",
            "flag",
            30,
        ),
        (
            "challenge_completed",
            "Challenge champion",
            "بطل التحدي",
            "Complete a challenge.",
            "أكمل تحديًا.",
            "medal",
            120,
        ),
        (
            "month_under_target",
            "Under target",
            "تحت الهدف",
            "Finish a month below your goal target.",
            "أنهِ شهرًا تحت هدفك.",
            "leaf",
            160,
        ),
        (
            "zero_waste_week",
            "Zero-waste week",
            "أسبوع بلا هدر",
            "Log no landfill waste for a week.",
            "لا تسجل نفايات مكب لمدة أسبوع.",
            "recycle",
            100,
        ),
        (
            "community_hero",
            "Community hero",
            "بطل المجتمع",
            "Reach the top three on the leaderboard.",
            "ادخل الثلاثة الأوائل في المتصدرين.",
            "star",
            220,
        ),
    ]
    result = {}
    for key, en, ar, desc_en, desc_ar, icon, points in data:
        row = Badge(
            key=key,
            title_en=en,
            title_ar=ar,
            description_en=desc_en,
            description_ar=desc_ar,
            icon=icon,
            criteria=desc_en,
            points=points,
        )
        db.session.add(row)
        result[key] = row
    db.session.flush()
    return result


def _seed_challenges(
    categories: dict[str, EmissionCategory], badges: dict[str, Badge]
) -> list[Challenge]:
    data = [
        (
            "weekly-records",
            "Five records this week",
            "خمسة سجلات هذا الأسبوع",
            "weekly",
            "record_count",
            5,
            60,
            "challenge_joined",
            date(2026, 6, 24),
            date(2026, 6, 30),
            None,
        ),
        (
            "monthly-electricity",
            "Shave 10% off electricity",
            "خفض الكهرباء 10%",
            "monthly",
            "reduction_percent",
            10,
            120,
            "challenge_completed",
            date(2026, 6, 1),
            date(2026, 6, 30),
            "electricity",
        ),
        (
            "public-transport",
            "Three low-car days",
            "ثلاثة أيام بلا سيارة",
            "weekly",
            "record_count",
            3,
            80,
            "community_hero",
            date(2026, 6, 1),
            date(2026, 6, 30),
            "transport",
        ),
        (
            "plant-based",
            "Five plant-based meals",
            "خمس وجبات نباتية",
            "monthly",
            "action_count",
            5,
            90,
            "zero_waste_week",
            date(2026, 6, 1),
            date(2026, 6, 30),
            "food",
        ),
        (
            "streak-30",
            "Thirty-day streak",
            "سلسلة ثلاثين يومًا",
            "community",
            "streak",
            30,
            200,
            "streak_30",
            date(2026, 6, 1),
            date(2026, 6, 30),
            None,
        ),
    ]
    rows = []
    for (
        key,
        en,
        ar,
        type_,
        target_type,
        target,
        points,
        badge_key,
        start,
        end,
        category_key,
    ) in data:
        row = Challenge(
            key=key,
            title_en=en,
            title_ar=ar,
            description_en=f"{en}. Progress is verified from your records where possible.",
            description_ar=f"{ar}. يتم التحقق من التقدم من سجلاتك حيثما أمكن.",
            type=type_,
            category_id=categories[category_key].id if category_key else None,
            target_type=target_type,
            target_value=target,
            points=points,
            badge_id=badges[badge_key].id,
            start_date=start,
            end_date=end,
            is_active=True,
        )
        db.session.add(row)
        rows.append(row)
    db.session.flush()
    return rows


def _seed_participation(
    users: dict[str, User], challenges: list[Challenge], badges: dict[str, Badge]
) -> None:
    sara = users["sara"]
    ahmad = users["ahmad"]
    rows = [
        (sara, challenges[0], 5, "completed"),
        (sara, challenges[1], 8, "in_progress"),
        (ahmad, challenges[2], 2, "in_progress"),
    ]
    for user, challenge, value, status in rows:
        participant = ChallengeParticipant(
            challenge_id=challenge.id,
            user_id=user.id,
            progress_value=value,
            status=status,
            joined_at=utcnow() - timedelta(days=5),
            completed_at=utcnow() if status == "completed" else None,
        )
        db.session.add(participant)
    for user, badge_keys in [
        (sara, ["first_record", "goal_set", "challenge_joined", "challenge_completed"]),
        (ahmad, ["first_record", "streak_7"]),
    ]:
        for key in badge_keys:
            db.session.add(
                UserBadge(
                    user_id=user.id,
                    badge_id=badges[key].id,
                    awarded_at=utcnow() - timedelta(days=RNG.randint(1, 30)),
                )
            )
    db.session.flush()


def _seed_points(users: dict[str, User], challenges: list[Challenge]) -> None:
    entries = []
    for index in range(20):
        user = [users["sara"], users["ahmad"], users["org"]][index % 3]
        entries.append(
            PointsLedger(
                user_id=user.id,
                points=RNG.choice([10, 20, 30, 40, 50, 60, 80, 120]),
                reason=RNG.choice(
                    [
                        "Logged a record",
                        "Completed an action",
                        "Joined a challenge",
                        "Weekly check-in",
                    ]
                ),
                reference_type="seed",
                reference_id=challenges[index % len(challenges)].id,
                created_at=datetime.combine(
                    date(2026, 6, 30) - timedelta(days=index * 2), time(10, 0)
                ),
            )
        )
    db.session.add_all(entries)
    db.session.flush()


def _seed_notifications(users: dict[str, User]) -> None:
    definitions = [
        (
            "sara",
            "goal",
            "Your June goal is live",
            "هدف يونيو جاهز",
            "You are tracking against a 10% reduction baseline.",
            "تتابع هدف خفض 10% من خط الأساس.",
            False,
            1,
        ),
        (
            "sara",
            "challenge",
            "Challenge completed",
            "اكتمل التحدي",
            "You finished the five-record week. 60 points added.",
            "أكملت أسبوع خمسة سجلات. أضيفت 60 نقطة.",
            True,
            2,
        ),
        (
            "sara",
            "plan",
            "A plan is ready",
            "الخطة جاهزة",
            "Four actions are waiting in A lighter June.",
            "أربعة إجراءات بانتظارك في خطة يونيو.",
            False,
            3,
        ),
        (
            "sara",
            "summary",
            "Weekly summary",
            "الملخص الأسبوعي",
            "Your latest calculated summary is ready.",
            "ملخصك المحسوب الأخير جاهز.",
            True,
            4,
        ),
        (
            "sara",
            "announcement",
            "Welcome to CarbonWise",
            "مرحبًا بك في كربونوايز",
            "Start with one utility bill or a manual record.",
            "ابدأ بفاتورة مرافق واحدة أو سجل يدوي.",
            True,
            5,
        ),
        (
            "ahmad",
            "alert",
            "Emissions increased",
            "ارتفعت الانبعاثات",
            "Your calculated emissions are higher than the previous period.",
            "انبعاثاتك المحسوبة أعلى من الفترة السابقة.",
            False,
            1,
        ),
        (
            "ahmad",
            "challenge",
            "New challenge",
            "تحدٍ جديد",
            "Three low-car days is open.",
            "تحدي ثلاثة أيام بلا سيارة متاح.",
            False,
            2,
        ),
        (
            "org",
            "summary",
            "Q2 report ready",
            "تقرير الربع الثاني جاهز",
            "The office reduction report is available.",
            "تقرير خفض المكتب متاح.",
            False,
            1,
        ),
    ]
    for user_key, type_, title_en, title_ar, body_en, body_ar, is_read, days in definitions:
        user = users[user_key]
        db.session.add(
            Notification(
                user_id=user.id,
                type=type_,
                title_en=title_en,
                title_ar=title_ar,
                body_en=body_en,
                body_ar=body_ar,
                is_read=is_read,
                action_url="/reports",
                created_at=utcnow() - timedelta(days=days),
                read_at=utcnow() - timedelta(days=days - 1) if is_read else None,
            )
        )
    db.session.flush()


def _seed_articles() -> None:
    articles = [
        (
            "understanding-carbon-footprint",
            "Understanding your carbon footprint",
            "فهم بصمتك الكربونية",
            "energy",
            "A practical introduction to the numbers behind CarbonWise.",
            "مقدمة عملية للأرقام وراء كربونوايز.",
        ),
        (
            "lower-electricity",
            "Seven ways to lower electricity emissions",
            "سبع طرق لخفض انبعاثات الكهرباء",
            "energy",
            "Lighting, standby, scheduling, and tariffs.",
            "الإضاءة والاستهلاك الخفي والجدولة والتعرفات.",
        ),
        (
            "transport-choices",
            "Transport choices that move the needle",
            "خيارات النقل الأكثر تأثيرًا",
            "transport",
            "Compare cars, buses, rail, and flights.",
            "قارن السيارات والحافلات والقطار والطيران.",
        ),
        (
            "food-and-climate",
            "Food and climate: a simple guide",
            "الطعام والمناخ: دليل بسيط",
            "food",
            "Why plant-based meals matter and how to start.",
            "لماذا تهم الوجبات النباتية وكيف تبدأ.",
        ),
        (
            "waste-not",
            "Waste not: a home routine",
            "لا تهدر: روتين منزلي",
            "waste",
            "Separate, plan, repair, and compost.",
            "افصل وخطط وأصلح وسمّد.",
        ),
        (
            "water-at-home",
            "Water at home",
            "المياه في المنزل",
            "water",
            "Leaks, fixtures, and heating.",
            "التسربات والتركيبات والتسخين.",
        ),
        (
            "green-workplace",
            "A greener workplace",
            "مكان عمل أكثر خضرة",
            "business",
            "A lightweight office reduction sprint.",
            "سبرنت خفيف لخفض انبعاثات المكتب.",
        ),
        (
            "reading-your-bill",
            "Reading your utility bill",
            "قراءة فاتورة المرافق",
            "energy",
            "Find the consumption value and billing period.",
            "اعثر على قيمة الاستهلاك وفترة الفاتورة.",
        ),
    ]
    for index, (slug, en, ar, category, summary_en, summary_ar) in enumerate(articles):
        db.session.add(
            Article(
                slug=slug,
                title_en=en,
                title_ar=ar,
                summary_en=summary_en,
                summary_ar=summary_ar,
                body_en=(
                    f"{summary_en}\n\nCarbonWise calculates emissions in the backend using a "
                    "documented factor and a snapshot on every record. AI can explain the "
                    "result, but it never replaces the calculation.\n\nTry one small action "
                    "this week and log the result. Consistency matters more than perfection."
                ),
                body_ar=(
                    f"{summary_ar}\n\nيحسب كربونوايز الانبعاثات في الخادم باستخدام عامل موثق "
                    "ولقطة محفوظة في كل سجل. يمكن للذكاء الاصطناعي شرح النتيجة، لكنه لا "
                    "يستبدل الحساب.\n\nجرّب إجراءً صغيرًا هذا الأسبوع وسجل النتيجة. الاستمرارية "
                    "أهم من الكمال."
                ),
                image_path=f"assets/images/articles/{slug}.png",
                category=category,
                is_published=True,
                published_at=utcnow() - timedelta(days=index * 3),
                sort_order=index,
            )
        )
    db.session.flush()


def _seed_ai(users: dict[str, User]) -> None:
    sara = users["sara"]
    conversation = AiConversation(
        user_id=sara.id,
        title="Why did my emissions change?",
        created_at=utcnow() - timedelta(days=2),
        updated_at=utcnow() - timedelta(days=2),
    )
    db.session.add(conversation)
    db.session.flush()
    db.session.add_all(
        [
            AiMessage(
                conversation_id=conversation.id,
                role="user",
                content="Why did my emissions change this month?",
                locale="en",
                created_at=utcnow() - timedelta(days=2, minutes=4),
            ),
            AiMessage(
                conversation_id=conversation.id,
                role="assistant",
                content=(
                    "Your calculated total is driven by electricity and road transport. "
                    "The largest category is shown in your report. A practical next step is "
                    "to replace two routine car trips this week and check the trend next month."
                ),
                locale="en",
                model="openrouter/free (seed demo)",
                tokens=420,
                created_at=utcnow() - timedelta(days=2, minutes=3),
            ),
        ]
    )
    features = ["assistant", "insights", "summary", "plan", "alternatives", "extraction"]
    statuses = ["success", "success", "success", "success", "error", "success"]
    for index in range(10):
        feature = features[index % len(features)]
        status = statuses[index % len(statuses)]
        db.session.add(
            AiUsage(
                user_id=sara.id if index % 2 == 0 else users["ahmad"].id,
                feature=feature,
                model="openrouter/free",
                prompt_tokens=300 + index * 30,
                completion_tokens=120 + index * 20,
                total_tokens=420 + index * 50,
                latency_ms=900 + index * 120,
                status=status,
                error_code="ai_invalid_output" if status == "error" else None,
                request_hash=hashlib.sha256(f"seed-{index}".encode()).hexdigest(),
                created_at=utcnow() - timedelta(days=index * 4),
            )
        )
    db.session.flush()


def _seed_audit(admins: list[Admin]) -> None:
    actions = [
        ("login", "admin", admins[0].id),
        ("update", "factor", 1),
        ("create", "challenge", 1),
        ("update", "article", 1),
        ("toggle", "category", 2),
        ("suspend", "user", 2),
        ("resolve", "ai_flag", 1),
        ("export", "report", None),
        ("create", "notification", None),
        ("update", "setting", 1),
    ]
    for index, (action, entity, entity_id) in enumerate(actions):
        db.session.add(
            AdminAuditLog(
                admin_id=admins[index % len(admins)].id,
                action=action,
                entity_type=entity,
                entity_id=entity_id,
                details_json=json.dumps({"seed": True}),
                created_at=utcnow() - timedelta(days=index),
            )
        )
    db.session.flush()


def _seed_settings() -> None:
    db.session.add_all(
        [
            AppSetting(
                key="demo.notice",
                value="Local demo. No real personal data. AI is best-effort and free-only.",
                updated_at=utcnow(),
            ),
            AppSetting(
                key="ai.disclaimer",
                value="AI explanations are separate from backend-calculated emission values.",
                updated_at=utcnow(),
            ),
        ]
    )
    db.session.flush()
