"""Prompt templates. Prompts are never logged."""

from __future__ import annotations

import json

LANGUAGE = {"en": "English", "ar": "Arabic (Modern Standard Arabic)"}

SYSTEM = (
    "You are CarbonWise, a sustainability assistant. The backend owns every emission "
    "calculation. You explain and recommend only. Never invent, alter, or extrapolate an "
    "emission number, factor, total, percentage, or saving. Use only the calculated context "
    "provided. If a number is missing, say it is unavailable. Be concise, practical, and "
    "non-judgmental. Do not give financial, legal, or medical advice. Reply in {language}."
)


def system(locale: str) -> str:
    return SYSTEM.format(language=LANGUAGE.get(locale, "English"))


def chat_context(context: dict) -> str:
    return (
        "Calculated context from the CarbonWise backend (the only numbers you may use):\n"
        + json.dumps(context, ensure_ascii=False)
        + "\nAnswer the user's question using this context. If the user asks for a number "
        "that is not present, say it is not available. End with one short practical next step."
    )


def insights(context: dict) -> str:
    return (
        "Write a short, useful interpretation of this backend-calculated report. "
        "Return ONLY JSON with keys: narrative (string, 2-4 sentences), observations "
        "(array of 2-4 short strings), opportunities (array of 2-4 short strings). "
        "Do not include any digits or numeric values in your text; the UI shows the "
        "backend numbers separately. Do not mention that you are an AI model.\n\n"
        "CALCULATED CONTEXT:\n" + json.dumps(context, ensure_ascii=False)
    )


def summary(context: dict) -> str:
    return (
        "Write a warm, concise sustainability summary of the calculated period. "
        "Return ONLY JSON with keys: narrative (string, 2-4 sentences), highlights "
        "(array of 2-4 short strings), next_steps (array of 2-4 short strings). "
        "Do not include digits. Do not invent numbers.\n\n"
        "CALCULATED CONTEXT:\n" + json.dumps(context, ensure_ascii=False)
    )


def plan(context: dict) -> str:
    return (
        "Create a practical 4-6 action reduction plan. Return ONLY JSON with keys: "
        "title (string), summary (string, 2-3 sentences), actions (array). Each action "
        "must have: title, description, category_key (one of the allowed keys), priority "
        "(high|medium|low), timeframe (this_week|this_month|this_quarter|ongoing). "
        "Do NOT include any numeric emission values, savings, percentages, or factors; "
        "the backend calculates those. Do not invent categories.\n\n"
        "CALCULATED CONTEXT:\n" + json.dumps(context, ensure_ascii=False)
    )


def alternatives(context: dict) -> str:
    return (
        "Rank the provided curated alternatives for this user. Return ONLY JSON with keys: "
        "ordered_keys (array of the provided keys, most relevant first) and rationale "
        "(one short sentence, no digits). Do not invent keys or numbers.\n\n"
        "CONTEXT:\n" + json.dumps(context, ensure_ascii=False)
    )


def extraction(locale: str) -> str:
    return (
        "Read this utility bill or receipt and return ONLY JSON with keys: vendor (string or "
        "null), billing_period (YYYY-MM or null), consumption_value (number or null), unit "
        "(string or null), confidence (number 0-1). Do not guess. If the image is unreadable, "
        "return nulls and confidence 0. This extraction is a suggestion; the user must confirm "
        "it before any record is created. Reply values in the original document language.\n"
        f"Preferred explanation language: {LANGUAGE.get(locale, 'English')}."
    )
