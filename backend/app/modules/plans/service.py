"""Reduction plan generation, fallback templates, and action tracking."""

from __future__ import annotations

from sqlalchemy import or_

from app.core.db import db, utcnow
from app.core.errors import ApiError
from app.core.periods import period_bounds
from app.modules.catalog.models import EmissionCategory
from app.modules.plans.models import PlanAction, ReductionPlan
from app.modules.records.queries import category_totals
from app.modules.users.models import User

CATEGORY_ASSUMPTIONS: dict[str, tuple[int, str, str]] = {
    "electricity": (
        10,
        "Backend assumption: a 10% reduction in current electricity emissions through "
        "lighting, standby, and scheduling changes. Not an AI estimate.",
        "افتراض من الخادم: خفض 10% من انبعاثات الكهرباء الحالية عبر الإضاءة والاستهلاك "
        "الخفي والجدولة. ليس تقديرًا من الذكاء الاصطناعي.",
    ),
    "transport": (
        15,
        "Backend assumption: a 15% reduction in current road-transport emissions by "
        "replacing some car trips. Not an AI estimate.",
        "افتراض من الخادم: خفض 15% من انبعاثات النقل البري الحالية عبر استبدال بعض "
        "رحلات السيارة. ليس تقديرًا من الذكاء الاصطناعي.",
    ),
    "flights": (
        10,
        "Backend assumption: a 10% reduction in current flight emissions by replacing "
        "one short-haul trip. Not an AI estimate.",
        "افتراض من الخادم: خفض 10% من انبعاثات الطيران الحالية عبر استبدال رحلة قصيرة. "
        "ليس تقديرًا من الذكاء الاصطناعي.",
    ),
    "water": (
        5,
        "Backend assumption: a 5% reduction in current water emissions through leak "
        "repair and low-flow fixtures. Not an AI estimate.",
        "افتراض من الخادم: خفض 5% من انبعاثات المياه الحالية عبر إصلاح التسربات "
        "وتركيبات التدفق المنخفض. ليس تقديرًا من الذكاء الاصطناعي.",
    ),
    "waste": (
        20,
        "Backend assumption: a 20% reduction in current waste emissions through "
        "recycling and food-waste separation. Not an AI estimate.",
        "افتراض من الخادم: خفض 20% من انبعاثات النفايات الحالية عبر إعادة التدوير "
        "وفصل مخلفات الطعام. ليس تقديرًا من الذكاء الاصطناعي.",
    ),
    "food": (
        10,
        "Backend assumption: a 10% reduction in current food emissions through "
        "plant-based meals and portion planning. Not an AI estimate.",
        "افتراض من الخادم: خفض 10% من انبعاثات الطعام الحالية عبر وجبات نباتية "
        "وتخطيط الحصص. ليس تقديرًا من الذكاء الاصطناعي.",
    ),
    "shopping": (
        5,
        "Backend assumption: a 5% reduction in current shopping emissions through "
        "repair, reuse, and second-hand choices. Not an AI estimate.",
        "افتراض من الخادم: خفض 5% من انبعاثات الشراء الحالية عبر الإصلاح وإعادة "
        "الاستخدام والاختيارات المستعملة. ليس تقديرًا من الذكاء الاصطناعي.",
    ),
}
DEFAULT_ASSUMPTION = (
    5,
    "Backend assumption: a 5% reduction in the selected category. Not an AI estimate.",
    "افتراض من الخادم: خفض 5% من الفئة المحددة. ليس تقديرًا من الذكاء الاصطناعي.",
)

TEMPLATES = {
    "electricity": {
        "en": (
            "Cut standby and lighting waste",
            "Switch to LED bulbs, unplug idle chargers, and schedule high-power appliances "
            "outside peak hours.",
        ),
        "ar": (
            "قلل استهلاك الإضاءة والأجهزة الخاملة",
            "استبدل المصابيح بمصابيح LED، وافصل الشواحن الخاملة، وجدول الأجهزة عالية "
            "الطاقة خارج ساعات الذروة.",
        ),
    },
    "transport": {
        "en": (
            "Replace two car trips per week",
            "Use public transport, carpool, or cycle for two routine trips each week.",
        ),
        "ar": (
            "استبدل رحلتين بالسيارة أسبوعيًا",
            "استخدم النقل العام أو مشاركة السيارة أو الدراجة في رحلتين معتادتين كل أسبوع.",
        ),
    },
    "flights": {
        "en": (
            "Choose rail or virtual meetings",
            "Replace one short-haul flight with rail where possible, or move the meeting online.",
        ),
        "ar": (
            "اختر القطار أو الاجتماعات الافتراضية",
            "استبدل رحلة طيران قصيرة بالقطار حيث أمكن، أو انقل الاجتماع إلى الإنترنت.",
        ),
    },
    "water": {
        "en": (
            "Fix leaks and reduce flow",
            "Check for leaks, install low-flow fixtures, and shorten shower time.",
        ),
        "ar": (
            "أصلح التسربات وقلل التدفق",
            "افحص التسربات، وركب تركيبات منخفضة التدفق، وقلل مدة الاستحمام.",
        ),
    },
    "waste": {
        "en": (
            "Separate recycling and food waste",
            "Set up labelled bins and plan meals to avoid discarded food.",
        ),
        "ar": (
            "افصل إعادة التدوير ومخلفات الطعام",
            "جهز حاويات موسومة وخطط الوجبات لتجنب هدر الطعام.",
        ),
    },
    "food": {
        "en": (
            "Add three plant-based meals",
            "Plan three plant-based meals this week and buy only the portions you will use.",
        ),
        "ar": (
            "أضف ثلاث وجبات نباتية",
            "خطط لثلاث وجبات نباتية هذا الأسبوع واشترِ الحصص التي ستستخدمها فقط.",
        ),
    },
    "shopping": {
        "en": (
            "Repair before replacing",
            "Repair one item or choose a second-hand option instead of buying new.",
        ),
        "ar": (
            "أصلح قبل الاستبدال",
            "أصلح قطعة واحدة أو اختر خيارًا مستعملًا بدلًا من الشراء الجديد.",
        ),
    },
}


def _query(user: User):
    if user.organization_id:
        return ReductionPlan.query.filter(
            or_(
                ReductionPlan.user_id == user.id,
                ReductionPlan.organization_id == user.organization_id,
            )
        )
    return ReductionPlan.query.filter(ReductionPlan.user_id == user.id)


def list_plans(user: User, status: str | None = None) -> list[dict]:
    query = _query(user)
    if status:
        query = query.filter(ReductionPlan.status == status)
    return [plan.to_dict() for plan in query.order_by(ReductionPlan.created_at.desc()).all()]


def get_plan(user: User, plan_id: int) -> ReductionPlan:
    plan = _query(user).filter(ReductionPlan.id == plan_id).first()
    if plan is None:
        raise ApiError("not_found", "Plan not found.", 404)
    return plan


def build_context(user: User, period: str = "month", goal_id: int | None = None) -> dict:
    start, end = period_bounds(period)
    categories = category_totals(user, start, end)
    total = sum(row["emissions_grams"] for row in categories)
    goal = None
    if goal_id:
        from app.modules.goals.service import progress

        goal = progress(user, goal_id)
    allowed = []
    for row in categories[:5]:
        assumption = CATEGORY_ASSUMPTIONS.get(row["key"], DEFAULT_ASSUMPTION)
        allowed.append(
            {
                "key": row["key"],
                "name_en": row["name_en"],
                "name_ar": row["name_ar"],
                "current_emissions_kg": row["emissions_kg"],
                "emissions_grams": row["emissions_grams"],
                "share_percent": row["share_percent"],
                "backend_assumption_percent": assumption[0],
            }
        )
    return {
        "period": {"from": start.isoformat(), "to": end.isoformat()},
        "total_kg": round(total / 1000, 2),
        "categories": allowed,
        "goal": (
            {
                "title": goal["title"],
                "target_percent": goal["target_percent"],
                "achieved_percent": goal["achieved_percent"],
                "days_left": goal["days_left"],
            }
            if goal
            else None
        ),
    }


def generate(user: User, payload) -> dict:
    context = build_context(user, payload.period, payload.goal_id)
    if not context["categories"]:
        raise ApiError(
            "validation_error",
            "Add consumption records before generating a plan.",
            422,
        )
    ai_payload = None
    model = None
    source = "template"
    try:
        from app.modules.ai import service as ai_service

        result = ai_service.generate_plan(context, payload.locale, user)
        ai_payload = result["payload"]
        model = result["model"]
        source = "ai"
    except Exception:  # noqa: BLE001
        ai_payload = None
    if not ai_payload:
        ai_payload = template_plan(context, payload.locale)
    plan = _create_plan(user, payload, context, ai_payload, source, model)
    return plan.to_dict()


def template_plan(context: dict, locale: str) -> dict:
    actions = []
    for item in context["categories"][:3]:
        template = TEMPLATES.get(item["key"], TEMPLATES["waste"])
        title, description = template["ar" if locale == "ar" else "en"]
        actions.append(
            {
                "title": title,
                "description": description,
                "category_key": item["key"],
                "priority": "high" if item["share_percent"] >= 35 else "medium",
                "timeframe": "this_month",
            }
        )
    return {
        "title": "خطة خفض الانبعاثات" if locale == "ar" else "Your reduction plan",
        "summary": (
            "خطة عملية مبنية على بياناتك المحسوبة في الخادم. التقديرات أدناه افتراضات "
            "موثقة، وليست أرقامًا من الذكاء الاصطناعي."
            if locale == "ar"
            else "A practical plan based on your backend-calculated data. The estimates "
            "below are documented assumptions, not AI-generated numbers."
        ),
        "actions": actions,
    }


def _create_plan(user, payload, context, ai_payload, source, model) -> ReductionPlan:
    plan = ReductionPlan(
        user_id=user.id,
        organization_id=user.organization_id if user.account_type == "organization" else None,
        goal_id=payload.goal_id,
        title=str(ai_payload.get("title") or "Reduction plan")[:200],
        summary=str(ai_payload.get("summary") or "")[:4000],
        locale=payload.locale,
        source=source,
        model=model,
        status="draft",
        generated_at=utcnow(),
    )
    db.session.add(plan)
    db.session.flush()
    category_map = {row["key"]: row for row in context["categories"]}
    for index, action in enumerate(ai_payload.get("actions", [])[:8]):
        category_key = str(action.get("category_key") or "").strip()
        category = EmissionCategory.query.filter_by(key=category_key).first()
        category_row = category_map.get(category_key)
        assumption = CATEGORY_ASSUMPTIONS.get(category_key, DEFAULT_ASSUMPTION)
        saving = None
        assumption_text = None
        if category_row:
            saving = round(category_row["emissions_grams"] * assumption[0] / 100)
            assumption_text = assumption[2] if payload.locale == "ar" else assumption[1]
        plan_action = PlanAction(
            plan_id=plan.id,
            title=str(action.get("title") or "Action")[:200],
            description=str(action.get("description") or "")[:2000],
            category_id=category.id if category else None,
            priority=(
                action.get("priority")
                if action.get("priority") in {"high", "medium", "low"}
                else "medium"
            ),
            timeframe=(
                action.get("timeframe")
                if action.get("timeframe") in {"this_week", "this_month", "this_quarter", "ongoing"}
                else "this_month"
            ),
            estimated_saving_grams=saving,
            saving_assumption=assumption_text,
            status="pending",
            sort_order=index,
        )
        db.session.add(plan_action)
    db.session.commit()
    return plan


def update_plan(user: User, plan_id: int, payload) -> dict:
    plan = get_plan(user, plan_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)
    db.session.commit()
    return plan.to_dict()


def update_action(user: User, plan_id: int, action_id: int, payload) -> dict:
    plan = get_plan(user, plan_id)
    action = PlanAction.query.filter_by(id=action_id, plan_id=plan.id).first()
    if action is None:
        raise ApiError("not_found", "Plan action not found.", 404)
    action.status = payload.status
    if payload.status == "completed":
        action.completed_at = utcnow()
        if plan.status == "draft":
            plan.status = "active"
    elif payload.status in {"pending", "in_progress"}:
        action.completed_at = None
    db.session.commit()
    return action.to_dict()


def progress(user: User, plan_id: int) -> dict:
    plan = get_plan(user, plan_id)
    actions = plan.actions
    completed = sum(1 for action in actions if action.status == "completed")
    estimated = sum(action.estimated_saving_grams or 0 for action in actions)
    return {
        "plan_id": plan.id,
        "title": plan.title,
        "status": plan.status,
        "actions_total": len(actions),
        "actions_completed": completed,
        "actions_in_progress": sum(1 for a in actions if a.status == "in_progress"),
        "progress_percent": round(completed / len(actions) * 100, 1) if actions else 0,
        "estimated_saving_grams": estimated,
        "estimated_saving_kg": round(estimated / 1000, 2),
        "note": (
            "Estimated savings are backend-calculated from documented category assumptions. "
            "They are not AI-generated emission values."
        ),
    }
