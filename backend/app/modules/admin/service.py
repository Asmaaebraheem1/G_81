"""Admin account lookup and audit logging."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from flask import request, session

from app.core.db import db, utcnow
from app.core.security import current_admin_id
from app.core.text import redact_pii
from app.modules.admin.models import Admin, AdminAuditLog


def current_admin() -> Admin | None:
    admin_id = current_admin_id()
    if admin_id is None:
        return None
    return db.session.get(Admin, admin_id)


def login_admin(admin: Admin) -> None:
    session.clear()
    session["admin_id"] = admin.id
    session["admin_role"] = admin.role
    session["admin_name"] = admin.name
    session.permanent = True
    admin.last_login_at = utcnow()
    db.session.commit()


def record(
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    details: dict | None = None,
) -> None:
    admin_id = current_admin_id()
    if admin_id is None:
        return
    safe = {}
    for key, value in (details or {}).items():
        safe[key] = redact_pii(str(value)) if isinstance(value, str) else value
    db.session.add(
        AdminAuditLog(
            admin_id=admin_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details_json=json.dumps(safe, ensure_ascii=False)[:4000] if safe else None,
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
    )
    db.session.commit()


def admin_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    return (forwarded.split(",")[0].strip() or request.remote_addr or "unknown")[:80]
