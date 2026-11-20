"""AI orchestration: grounding, validation, usage, caching, and fallbacks."""

from __future__ import annotations

import base64
import hashlib
import json
import time
from datetime import date, datetime
from datetime import time as dt_time
from pathlib import Path

from flask import current_app
from pydantic import ValidationError
from sqlalchemy import func

from app.core.db import db, utcnow
from app.core.errors import ApiError
from app.core.periods import demo_today, period_bounds
from app.core.rate_limit import ai_limiter
from app.core.text import excerpt, redact_pii
from app.modules.ai import client, prompts
from app.modules.ai.errors import AiUnavailable
from app.modules.ai.models import (
    AiConversation,
    AiFlaggedResponse,
    AiMessage,
    AiUsage,
)
from app.modules.ai.schemas import (
    AlternativeAI,
    ExtractionAI,
    InsightAI,
    PlanAI,
    SummaryAI,
)
from app.modules.alternatives.models import Alternative
from app.modules.catalog.models import EmissionCategory
from app.modules.records.queries import category_totals
from app.modules.reports import service as reports
from app.modules.users.models import User

DISCLAIMER = (
    "AI explanation of backend-calculated values. Estimates only; not professional "
    "environmental, financial, or legal advice."
)


def _screenshot_mode() -> bool:
    return bool(current_app.config.get("AI_SCREENSHOT_MODE"))


def _hash(*parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _today_start() -> datetime:
    return datetime.combine(demo_today(), dt_time.min)


def _budget_used() -> int:
    value = (
        db.session.query(func.coalesce(func.sum(AiUsage.total_tokens), 0))
        .filter(AiUsage.created_at >= _today_start())
        .scalar()
    )
    return int(value or 0)


def _record_usage(
    *,
    user_id: int | None,
    feature: str,
    model: str,
    usage: dict,
    latency_ms: int,
    status: str,
    error_code: str | None,
    request_hash: str,
) -> None:
    row = AiUsage(
        user_id=user_id,
        feature=feature,
        model=model or "openrouter/free",
        prompt_tokens=int(usage.get("prompt_tokens") or 0),
        completion_tokens=int(usage.get("completion_tokens") or 0),
        total_tokens=int(usage.get("total_tokens") or 0),
        latency_ms=max(0, latency_ms),
        status=status,
        error_code=error_code,
        request_hash=request_hash,
        created_at=utcnow(),
    )
    db.session.add(row)
    try:
        db.session.commit()
    except Exception:  # noqa: BLE001
        db.session.rollback()


def _ensure_available(user: User, feature: str) -> None:
    if _screenshot_mode():
        return
    if not client.is_enabled():
        raise AiUnavailable(
            "ai_disabled",
            "AI is disabled because no OpenRouter key is configured. "
            "All calculated features still work.",
            503,
        )
    ai_limiter.check(f"ai:{user.id}")
    budget = int(current_app.config.get("AI_DAILY_TOKEN_BUDGET", 200000))
    if budget > 0 and _budget_used() >= budget:
        raise AiUnavailable(
            "ai_budget_exhausted",
            "The daily free-AI budget is exhausted. Calculated features still work.",
            503,
        )


def _parse_json(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("No JSON object found")
    value = json.loads(text[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return value


def _has_numeric_value(text: str) -> bool:
    cleaned = (text or "").replace("CO2", "").replace("CO₂", "")
    return any(char.isdigit() for char in cleaned)


def _assert_no_numbers(payload: dict) -> None:
    def walk(value):
        if isinstance(value, str):
            if _has_numeric_value(value):
                raise ValueError("AI text must not contain numeric values")
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)


def _call_structured(
    *,
    feature: str,
    user: User,
    locale: str,
    prompt: str,
    schema,
    request_hash: str,
    max_tokens: int = 1200,
):
    _ensure_available(user, feature)
    started = time.monotonic()
    try:
        result = client.chat_completion(
            [
                {"role": "system", "content": prompts.system(locale)},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=max_tokens,
        )
    except AiUnavailable as exc:
        _record_usage(
            user_id=user.id,
            feature=feature,
            model=client.model_name(),
            usage={},
            latency_ms=int((time.monotonic() - started) * 1000),
            status="error",
            error_code=exc.code,
            request_hash=request_hash,
        )
        raise
    latency = int((time.monotonic() - started) * 1000)
    try:
        payload = schema.model_validate(_parse_json(result["content"]))
        payload_dict = payload.model_dump()
        _assert_no_numbers(payload_dict)
    except (ValueError, ValidationError) as exc:
        _record_usage(
            user_id=user.id,
            feature=feature,
            model=result["model"],
            usage=result["usage"],
            latency_ms=latency,
            status="error",
            error_code="ai_invalid_output",
            request_hash=request_hash,
        )
        raise AiUnavailable(
            "ai_invalid_output",
            "The AI returned an invalid structured response. A calculated fallback is available.",
            502,
        ) from exc
    _record_usage(
        user_id=user.id,
        feature=feature,
        model=result["model"],
        usage=result["usage"],
        latency_ms=latency,
        status="success",
        error_code=None,
        request_hash=request_hash,
    )
    return {"payload": payload_dict, "model": result["model"], "usage": result["usage"]}


def status(user: User) -> dict:
    budget = int(current_app.config.get("AI_DAILY_TOKEN_BUDGET", 200000))
    return {
        "enabled": client.is_enabled() or _screenshot_mode(),
        "configured": bool(current_app.config.get("OPENROUTER_API_KEY")),
        "model": "openrouter/free",
        "vision": "best_effort",
        "budget": {
            "daily_token_limit": budget,
            "used_today": _budget_used(),
            "remaining": max(0, budget - _budget_used()),
        },
        "disclaimer": DISCLAIMER,
    }


def build_chat_context(user: User) -> dict:
    dash = reports.dashboard(user, "month")
    trend = reports.trend(user, 3)
    goals = dash.get("goals", [])
    return {
        "period": dash["period"],
        "total_kg": dash["totals"]["emissions_kg"],
        "records": dash["totals"]["records"],
        "previous_total_kg": dash["previous"]["emissions_kg"],
        "change_percent": dash["change"]["percent"],
        "change_direction": dash["change"]["direction"],
        "top_categories": [
            {
                "name_en": row["name_en"],
                "name_ar": row["name_ar"],
                "emissions_kg": row["emissions_kg"],
                "share_percent": row["share_percent"],
            }
            for row in dash["categories"][:4]
        ],
        "recent_months": [
            {
                "month": point["month"],
                "emissions_kg": point["emissions_kg"],
            }
            for point in trend["points"]
        ],
        "goals": [
            {
                "title": goal["title"],
                "achieved_percent": goal["achieved_percent"],
                "days_left": goal["days_left"],
                "status": goal["status"],
            }
            for goal in goals[:3]
        ],
    }


def _english_change_phrase(change) -> str:
    text = str(change)
    if text.startswith("-"):
        return f"a {text[1:]}% decrease compared with the previous period"
    return f"a {text}% increase compared with the previous period"


def _fallback_chat_text(context: dict, locale: str) -> str:
    top = context["top_categories"][0] if context["top_categories"] else None
    if locale == "ar":
        text = (
            f"إجمالي انبعاثاتك المحسوبة لهذه الفترة هو {context['total_kg']} كجم CO2e، "
            f"بمقارنة {context['change_percent']}% مع الفترة السابقة. "
        )
        if top:
            text += f"أكبر مصدر هو {top['name_ar']} بنحو {top['emissions_kg']} كجم. "
        text += "خطوة عملية: اختر ثلاث عادات صغيرة من خطتك وابدأ بها هذا الأسبوع."
        return text
    text = (
        f"Your calculated emissions for this period are {context['total_kg']} kg CO2e, "
        f"{_english_change_phrase(context['change_percent'])}. "
    )
    if top:
        text += f"The largest source is {top['name_en']} at about {top['emissions_kg']} kg. "
    text += (
        "A practical next step is to pick three small habits from your plan and start this week."
    )
    return text


def _canned_chat(context: dict, locale: str) -> str:
    return _fallback_chat_text(context, locale)


def chat(user: User, payload) -> dict:
    context = build_chat_context(user)
    if not client.is_enabled() and not _screenshot_mode():
        raise AiUnavailable(
            "ai_disabled",
            "AI is disabled because no OpenRouter key is configured. "
            "The calculated summary is still available.",
            503,
            details={"fallback": context, "disclaimer": DISCLAIMER},
        )
    conversation = None
    if payload.conversation_id:
        conversation = AiConversation.query.filter_by(
            id=payload.conversation_id, user_id=user.id
        ).first()
        if conversation is None:
            raise ApiError("not_found", "Conversation not found.", 404)
    if conversation is None:
        conversation = AiConversation(
            user_id=user.id,
            title=excerpt(payload.message, 70),
        )
        db.session.add(conversation)
        db.session.flush()
    user_message = AiMessage(
        conversation_id=conversation.id,
        role="user",
        content=payload.message,
        locale=payload.locale,
        created_at=utcnow(),
    )
    db.session.add(user_message)
    conversation.updated_at = utcnow()
    db.session.commit()

    history_rows = (
        AiMessage.query.filter_by(conversation_id=conversation.id)
        .order_by(AiMessage.created_at.desc(), AiMessage.id.desc())
        .limit(10)
        .all()
    )
    history = [
        {"role": message.role, "content": message.content}
        for message in reversed(history_rows)
        if message.id != user_message.id
    ][-8:]

    request_hash = _hash("assistant", user.id, payload.message, context)
    if _screenshot_mode():
        content = _canned_chat(context, payload.locale)
        model = "openrouter/free (screenshot mode)"
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    else:
        _ensure_available(user, "assistant")
        started = time.monotonic()
        try:
            result = client.chat_completion(
                [
                    {
                        "role": "system",
                        "content": prompts.system(payload.locale)
                        + "\n\n"
                        + prompts.chat_context(context),
                    },
                    *history,
                    {"role": "user", "content": payload.message},
                ],
                temperature=0.3,
                max_tokens=700,
            )
        except AiUnavailable as exc:
            _record_usage(
                user_id=user.id,
                feature="assistant",
                model=client.model_name(),
                usage={},
                latency_ms=int((time.monotonic() - started) * 1000),
                status="error",
                error_code=exc.code,
                request_hash=request_hash,
            )
            raise AiUnavailable(
                exc.code, exc.message, exc.status, {**exc.details, "fallback": context}
            ) from exc
        content = result["content"]
        model = result["model"]
        usage = result["usage"]
        _record_usage(
            user_id=user.id,
            feature="assistant",
            model=model,
            usage=usage,
            latency_ms=int((time.monotonic() - started) * 1000),
            status="success",
            error_code=None,
            request_hash=request_hash,
        )
    assistant_message = AiMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=content,
        locale=payload.locale,
        model=model,
        tokens=int(usage.get("total_tokens") or 0) if usage else 0,
        created_at=utcnow(),
    )
    db.session.add(assistant_message)
    conversation.updated_at = utcnow()
    db.session.commit()
    return {
        "conversation_id": conversation.id,
        "message_id": assistant_message.id,
        "content": content,
        "model": model,
        "context": context,
        "disclaimer": DISCLAIMER,
    }


def list_conversations(user: User) -> list[dict]:
    rows = (
        AiConversation.query.filter_by(user_id=user.id)
        .order_by(AiConversation.updated_at.desc())
        .limit(50)
        .all()
    )
    return [row.to_dict() for row in rows]


def get_conversation(user: User, conversation_id: int) -> dict:
    conversation = AiConversation.query.filter_by(id=conversation_id, user_id=user.id).first()
    if conversation is None:
        raise ApiError("not_found", "Conversation not found.", 404)
    messages = (
        AiMessage.query.filter_by(conversation_id=conversation.id)
        .order_by(AiMessage.created_at, AiMessage.id)
        .all()
    )
    data = conversation.to_dict()
    data["messages"] = [message.to_dict() for message in messages]
    return data


def delete_conversation(user: User, conversation_id: int) -> dict:
    conversation = AiConversation.query.filter_by(id=conversation_id, user_id=user.id).first()
    if conversation is None:
        raise ApiError("not_found", "Conversation not found.", 404)
    # Keep moderation records, but detach them from messages that are about to
    # be removed so the foreign key remains valid.
    message_ids = [message.id for message in conversation.messages]
    if message_ids:
        AiFlaggedResponse.query.filter(AiFlaggedResponse.message_id.in_(message_ids)).update(
            {"message_id": None}, synchronize_session=False
        )
    db.session.delete(conversation)
    db.session.commit()
    return {"deleted": True, "id": conversation_id}


def _report_context(user: User, period: str, from_date: date | None, to_date: date | None):
    start, end = period_bounds(
        period,
        from_date.isoformat() if from_date else None,
        to_date.isoformat() if to_date else None,
    )
    dash = reports.dashboard(user, period, start.isoformat(), end.isoformat())
    comparison = reports.comparison(user, period, start.isoformat(), end.isoformat())
    top = reports.top_activities(user, period, start.isoformat(), end.isoformat(), 5)
    return {
        "period": {"from": start.isoformat(), "to": end.isoformat()},
        "totals": dash["totals"],
        "previous": dash["previous"],
        "change": dash["change"],
        "categories": dash["categories"],
        "top_activities": top["activities"],
        "comparison": comparison,
        "trend": reports.trend(user, 6),
        "goals": dash["goals"],
    }


def _catalog_opportunities(user: User, limit: int = 4) -> list[dict]:
    totals = category_totals(user, *period_bounds("month"))
    keys = [row["key"] for row in totals[:3]]
    if not keys:
        return []
    categories = EmissionCategory.query.filter(EmissionCategory.key.in_(keys)).all()
    category_ids = [category.id for category in categories]
    alternatives = (
        Alternative.query.filter_by(is_active=True)
        .filter(Alternative.category_id.in_(category_ids))
        .order_by(Alternative.sort_order)
        .limit(limit)
        .all()
    )
    return [
        {
            "key": item.key,
            "title_en": item.title_en,
            "title_ar": item.title_ar,
            "description_en": item.description_en,
            "description_ar": item.description_ar,
            "assumption_en": item.assumption_en,
            "assumption_ar": item.assumption_ar,
            "source": "catalog",
        }
        for item in alternatives
    ]


def _rules_narrative(context: dict, locale: str) -> str:
    total = context["totals"]["emissions_kg"]
    change = context["change"]["percent"]
    top = context["categories"][0] if context["categories"] else None
    if locale == "ar":
        text = f"بلغ إجمالي انبعاثاتك المحسوبة {total} كجم CO2e في هذه الفترة"
        if change:
            change_text = str(change)
            if change_text.startswith("-"):
                text += f"، بانخفاض {change_text[1:]}% عن الفترة السابقة"
            else:
                text += f"، بارتفاع {change_text}% عن الفترة السابقة"
        if top:
            text += f". أكبر مصدر هو {top['name_ar']} بنسبة {top['share_percent']}%"
        return text + ". راجع أفضل الأنشطة واختر إجراءً واحدًا قابلًا للتنفيذ."
    text = f"Your calculated emissions were {total} kg CO2e in this period"
    if change:
        change_text = str(change)
        if change_text.startswith("-"):
            text += f", a {change_text[1:]}% decrease from the previous period"
        else:
            text += f", a {change_text}% increase from the previous period"
    if top:
        text += f". The largest source was {top['name_en']} at {top['share_percent']}%"
    return text + ". Review the top activities and choose one practical action."


def insights(user: User, payload) -> dict:
    context = _report_context(user, payload.period, payload.from_date, payload.to_date)
    ai_payload = None
    model = None
    source = "rules"
    if _screenshot_mode():
        ai_payload = {
            "narrative": (
                "Your emissions are driven by everyday energy and transport choices. "
                "The pattern is stable enough to act on now."
                if payload.locale == "en"
                else "تنبع انبعاثاتك من خيارات الطاقة والنقل اليومية. النمط مستقر بما يكفي للبدء الآن."
            ),
            "observations": (
                [
                    "The largest category deserves the first action.",
                    "Small repeated changes beat one-off efforts.",
                ]
                if payload.locale == "en"
                else [
                    "الفئة الأكبر تستحق الإجراء الأول.",
                    "التغييرات الصغيرة المتكررة أفضل من الجهد لمرة واحدة.",
                ]
            ),
            "opportunities": (
                [
                    "Start with the action that needs no new purchase.",
                    "Schedule a weekly check-in to keep momentum.",
                ]
                if payload.locale == "en"
                else [
                    "ابدأ بالإجراء الذي لا يحتاج شراءً جديدًا.",
                    "حدد مراجعة أسبوعية للحفاظ على الزخم.",
                ]
            ),
        }
        model = "openrouter/free (screenshot mode)"
        source = "ai"
    elif client.is_enabled():
        try:
            result = _call_structured(
                feature="insights",
                user=user,
                locale=payload.locale,
                prompt=prompts.insights(context),
                schema=InsightAI,
                request_hash=_hash("insights", user.id, context),
                max_tokens=700,
            )
            ai_payload = result["payload"]
            model = result["model"]
            source = "ai"
        except AiUnavailable:
            ai_payload = None
    if ai_payload is None:
        ai_payload = {
            "narrative": _rules_narrative(context, payload.locale),
            "observations": [],
            "opportunities": [],
        }
        source = "rules"
    top_sources = [
        {
            "name_en": row["name_en"],
            "name_ar": row["name_ar"],
            "emissions_grams": row["emissions_grams"],
            "emissions_kg": row["emissions_kg"],
            "share_percent": row["share_percent"],
        }
        for row in context["categories"][:5]
    ]
    changes = [
        {
            "category_id": row["category_id"],
            "name_en": row["name_en"],
            "name_ar": row["name_ar"],
            "change_grams": row["change_grams"],
            "change_percent": row["change_percent"],
        }
        for row in context["comparison"]["categories"][:5]
    ]
    opportunities = _catalog_opportunities(user)
    for text in ai_payload.get("opportunities", [])[:3]:
        opportunities.append({"title_en": text, "title_ar": text, "source": "ai_text"})
    return {
        "source": source,
        "model": model,
        "period": context["period"],
        "narrative": ai_payload["narrative"],
        "observations": ai_payload.get("observations", []),
        "top_sources": top_sources,
        "changes": changes,
        "comparisons": context["trend"]["points"],
        "opportunities": opportunities,
        "calculated_context": {
            "total_kg": context["totals"]["emissions_kg"],
            "previous_kg": context["previous"]["emissions_kg"],
            "change_percent": context["change"]["percent"],
        },
        "disclaimer": DISCLAIMER,
    }


def summary(user: User, payload) -> dict:
    context = _report_context(user, payload.period, None, None)
    ai_payload = None
    model = None
    source = "rules"
    if _screenshot_mode():
        ai_payload = {
            "narrative": (
                "This period shows a clear starting point: one category dominates, and "
                "consistent small actions can move the trend."
                if payload.locale == "en"
                else "تُظهر هذه الفترة نقطة بداية واضحة: فئة واحدة تهيمن، ويمكن للإجراءات الصغيرة المتسقة تغيير الاتجاه."
            ),
            "highlights": (
                [
                    "Your data is complete enough for a meaningful comparison.",
                    "A focused plan will be more useful than many scattered actions.",
                ]
                if payload.locale == "en"
                else [
                    "بياناتك كافية لإجراء مقارنة ذات معنى.",
                    "الخطة المركزة ستكون أفضل من إجراءات كثيرة متفرقة.",
                ]
            ),
            "next_steps": (
                [
                    "Open your reduction plan and complete one action.",
                    "Set a goal if you do not have one yet.",
                ]
                if payload.locale == "en"
                else ["افتح خطة الخفض وأكمل إجراءً واحدًا.", "حدد هدفًا إن لم يكن لديك هدف بعد."]
            ),
        }
        model = "openrouter/free (screenshot mode)"
        source = "ai"
    elif client.is_enabled():
        try:
            result = _call_structured(
                feature="summary",
                user=user,
                locale=payload.locale,
                prompt=prompts.summary(context),
                schema=SummaryAI,
                request_hash=_hash("summary", user.id, context),
                max_tokens=600,
            )
            ai_payload = result["payload"]
            model = result["model"]
            source = "ai"
        except AiUnavailable:
            ai_payload = None
    if ai_payload is None:
        ai_payload = {
            "narrative": _rules_narrative(context, payload.locale),
            "highlights": [],
            "next_steps": [],
        }
        source = "rules"
    return {
        "source": source,
        "model": model,
        "period": context["period"],
        "narrative": ai_payload["narrative"],
        "highlights": ai_payload.get("highlights", []),
        "next_steps": ai_payload.get("next_steps", []),
        "totals": context["totals"],
        "previous": context["previous"],
        "change": context["change"],
        "categories": context["categories"],
        "disclaimer": DISCLAIMER,
    }


def generate_plan(context: dict, locale: str, user: User) -> dict:
    if _screenshot_mode():
        actions = []
        for row in context["categories"][:3]:
            actions.append(
                {
                    "title": (
                        f"Improve {row['name_en']}" if locale == "en" else f"حسّن {row['name_ar']}"
                    ),
                    "description": (
                        "Choose one repeatable change and track it for a month."
                        if locale == "en"
                        else "اختر تغييرًا واحدًا قابلًا للتكرار وتابعه لمدة شهر."
                    ),
                    "category_key": row["key"],
                    "priority": "high" if row["share_percent"] >= 35 else "medium",
                    "timeframe": "this_month",
                }
            )
        return {
            "payload": {
                "title": "Your reduction plan" if locale == "en" else "خطة الخفض الخاصة بك",
                "summary": (
                    "A focused plan built from your calculated categories."
                    if locale == "en"
                    else "خطة مركزة مبنية على فئاتك المحسوبة."
                ),
                "actions": actions,
            },
            "model": "openrouter/free (screenshot mode)",
            "usage": {},
        }
    if not client.is_enabled():
        raise AiUnavailable("ai_disabled", "AI is disabled.", 503)
    allowed = {row["key"] for row in context["categories"]}
    result = _call_structured(
        feature="plan",
        user=user,
        locale=locale,
        prompt=prompts.plan(context),
        schema=PlanAI,
        request_hash=_hash("plan", user.id, context),
        max_tokens=1200,
    )
    for action in result["payload"]["actions"]:
        if action["category_key"] not in allowed:
            raise AiUnavailable(
                "ai_invalid_output",
                "The AI proposed a category that is not in the calculated context.",
                502,
            )
    return result


def _user_from_context(context: dict) -> User:
    """Deprecated helper kept for compatibility with early plan callers."""
    return _CurrentUserProxy(context)  # type: ignore[return-value]


class _CurrentUserProxy:
    def __init__(self, context: dict) -> None:
        self.id = 0
        self.context = context


def recommend_alternatives(user: User, locale: str = "en") -> dict:
    totals = category_totals(user, *period_bounds("month"))
    top_keys = [row["key"] for row in totals[:3]]
    alternatives = (
        Alternative.query.filter_by(is_active=True)
        .order_by(Alternative.sort_order, Alternative.title_en)
        .all()
    )
    if not alternatives:
        return {"source": "rules", "items": [], "rationale": ""}
    categories = {
        category.id: category.key
        for category in EmissionCategory.query.filter(
            EmissionCategory.id.in_([a.category_id for a in alternatives if a.category_id])
        ).all()
    }
    items = []
    for item in alternatives:
        data = item.to_dict()
        data["category_key"] = categories.get(item.category_id)
        data["recommended"] = data["category_key"] in top_keys
        items.append(data)
    items.sort(key=lambda x: (not x["recommended"], x["id"]))
    if not client.is_enabled() and not _screenshot_mode():
        return {"source": "rules", "items": items[:8], "rationale": ""}
    context = {
        "top_category_keys": top_keys,
        "alternatives": [
            {
                "key": item["key"],
                "title_en": item["title_en"],
                "title_ar": item["title_ar"],
                "category_key": item["category_key"],
            }
            for item in items[:12]
        ],
    }
    if _screenshot_mode():
        return {
            "source": "ai",
            "items": items[:8],
            "rationale": (
                "Start with the alternatives that match your largest calculated category."
                if locale == "en"
                else "ابدأ بالبدائل التي تطابق أكبر فئة محسوبة لديك."
            ),
        }
    try:
        result = _call_structured(
            feature="alternatives",
            user=user,
            locale=locale,
            prompt=prompts.alternatives(context),
            schema=AlternativeAI,
            request_hash=_hash("alternatives", user.id, context),
            max_tokens=500,
        )
        order = {key: index for index, key in enumerate(result["payload"]["ordered_keys"])}
        valid = {item["key"] for item in items}
        items.sort(key=lambda x: (order.get(x["key"], 999), x["id"]))
        items = [item for item in items if item["key"] in valid]
        return {
            "source": "ai",
            "items": items[:8],
            "rationale": result["payload"].get("rationale", ""),
        }
    except AiUnavailable:
        return {"source": "rules", "items": items[:8], "rationale": ""}


def _image_data_url(path: Path, mime_type: str) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _pdf_text(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages[:5]:
        parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()


def extract_document(user: User, document) -> dict:
    if not document.ai_consent:
        raise ApiError(
            "consent_required",
            "Confirm consent before sending this document to the AI provider.",
            422,
        )
    if _screenshot_mode():
        fields = {
            "vendor": "City Electric",
            "billing_period": "2026-05",
            "consumption_value": 120.5,
            "unit": "kWh",
            "confidence": 0.91,
        }
        document.status = "extracted"
        document.extraction_json = json.dumps(fields)
        document.extraction_model = "openrouter/free (screenshot mode)"
        db.session.commit()
        return {
            "status": "extracted",
            "model": document.extraction_model,
            "fields": fields,
            "disclaimer": DISCLAIMER,
        }
    if not client.is_enabled():
        raise AiUnavailable(
            "ai_disabled",
            "AI extraction is disabled because no OpenRouter key is configured. "
            "Enter the values manually.",
            503,
            details={"fallback": "manual_entry"},
        )
    root = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    path = (root / document.storage_path).resolve()
    if root not in path.parents or not path.exists():
        raise ApiError("not_found", "The stored file could not be found.", 404)
    request_hash = _hash("extraction", user.id, document.id, document.storage_path)
    started = time.monotonic()
    try:
        if document.mime_type.startswith("image/"):
            messages = [
                {"role": "system", "content": prompts.system("en")},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompts.extraction("en")},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": _image_data_url(path, document.mime_type),
                            },
                        },
                    ],
                },
            ]
        elif document.mime_type == "application/pdf":
            text = _pdf_text(path)
            if not text:
                raise AiUnavailable(
                    "vision_unavailable",
                    "This PDF has no readable text. Enter the values manually.",
                    422,
                    details={"fallback": "manual_entry"},
                )
            messages = [
                {"role": "system", "content": prompts.system("en")},
                {
                    "role": "user",
                    "content": prompts.extraction("en") + "\n\nDOCUMENT TEXT:\n" + text[:12000],
                },
            ]
        else:
            raise AiUnavailable(
                "vision_unavailable",
                "This file type cannot be read by the free model. Enter the values manually.",
                422,
                details={"fallback": "manual_entry"},
            )
        result = client.chat_completion(messages, temperature=0, max_tokens=600)
        payload = ExtractionAI.model_validate(_parse_json(result["content"]))
        fields = payload.model_dump()
        document.status = "extracted"
        document.extraction_json = json.dumps(fields)
        document.extraction_model = result["model"]
        db.session.commit()
        _record_usage(
            user_id=user.id,
            feature="extraction",
            model=result["model"],
            usage=result["usage"],
            latency_ms=int((time.monotonic() - started) * 1000),
            status="success",
            error_code=None,
            request_hash=request_hash,
        )
        return {
            "status": "extracted",
            "model": result["model"],
            "fields": fields,
            "disclaimer": DISCLAIMER,
        }
    except AiUnavailable as exc:
        document.status = "failed"
        document.extraction_json = json.dumps({"error": exc.code})
        db.session.commit()
        _record_usage(
            user_id=user.id,
            feature="extraction",
            model=client.model_name(),
            usage={},
            latency_ms=int((time.monotonic() - started) * 1000),
            status="error",
            error_code=exc.code,
            request_hash=request_hash,
        )
        raise
    except (ValueError, ValidationError) as exc:
        document.status = "failed"
        document.extraction_json = json.dumps({"error": "ai_invalid_output"})
        db.session.commit()
        _record_usage(
            user_id=user.id,
            feature="extraction",
            model=client.model_name(),
            usage={},
            latency_ms=int((time.monotonic() - started) * 1000),
            status="error",
            error_code="ai_invalid_output",
            request_hash=request_hash,
        )
        raise AiUnavailable(
            "ai_invalid_output",
            "The extraction result was not valid. Enter the values manually.",
            502,
            details={"fallback": "manual_entry"},
        ) from exc


def flag_response(user: User, payload) -> dict:
    message = (
        AiMessage.query.join(AiConversation, AiMessage.conversation_id == AiConversation.id)
        .filter(AiMessage.id == payload.message_id, AiConversation.user_id == user.id)
        .first()
    )
    if message is None:
        raise ApiError("not_found", "AI message not found.", 404)
    row = AiFlaggedResponse(
        user_id=user.id,
        message_id=message.id,
        reason=payload.reason,
        status="open",
        admin_notes=redact_pii(payload.notes or "")[:2000],
        created_at=utcnow(),
    )
    db.session.add(row)
    db.session.commit()
    return {
        "id": row.id,
        "status": row.status,
        "message": "Thank you. An admin will review this response.",
    }
