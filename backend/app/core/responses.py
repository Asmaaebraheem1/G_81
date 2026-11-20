"""Pagination helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from flask import request


def parse_pagination(default_per_page: int = 20, max_per_page: int = 50):
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = int(request.args.get("per_page", default_per_page))
    except (TypeError, ValueError):
        per_page = default_per_page
    per_page = max(1, min(per_page, max_per_page))
    return page, per_page


def paginated(
    items: list[Any],
    page: int,
    per_page: int,
    total: int,
    serializer: Callable[[Any], Any],
):
    pages = (total + per_page - 1) // per_page if total else 0
    return {
        "data": [serializer(item) for item in items],
        "meta": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
        },
    }
