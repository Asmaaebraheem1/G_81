"""Text helpers: slugs and PII redaction."""

from __future__ import annotations

import re
import unicodedata

_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")
_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


def slugify(value: str, fallback: str = "item") -> str:
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value[:180] or fallback


def unique_slug(model, base: str, column_name: str = "slug") -> str:
    """Return a slug that is unique for a model, appending -2, -3, ..."""
    base = slugify(base)
    candidate = base
    index = 2
    while model.query.filter(getattr(model, column_name) == candidate).first() is not None:
        candidate = f"{base}-{index}"
        index += 1
    return candidate


def redact_pii(text: str) -> str:
    text = _EMAIL_RE.sub("[email]", text or "")
    text = _CARD_RE.sub("[number]", text)
    text = _PHONE_RE.sub("[phone]", text)
    return text


def excerpt(text: str, length: int = 80) -> str:
    cleaned = " ".join((text or "").split())
    return cleaned if len(cleaned) <= length else cleaned[: length - 1].rstrip() + "…"
