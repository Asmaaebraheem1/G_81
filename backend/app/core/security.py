"""Password hashing and admin session guards."""

from __future__ import annotations

from functools import wraps

from flask import flash, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    return check_password_hash(password_hash, password)


def current_admin_id() -> int | None:
    raw = session.get("admin_id")
    return int(raw) if raw is not None else None


def current_admin_role() -> str | None:
    return session.get("admin_role")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_admin_id() is None:
            flash("Please sign in.", "error")
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def role_required(*roles: str):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if current_admin_id() is None:
                flash("Please sign in.", "error")
                return redirect(url_for("admin.login", next=request.path))
            if current_admin_role() not in roles:
                return (
                    """
                    <!doctype html><html><body style="font-family:sans-serif;padding:2rem">
                    <h1>403 — Permission denied</h1>
                    <p>Your admin role cannot access this page.</p>
                    <p><a href="/admin/">Back to dashboard</a></p>
                    </body></html>
                    """,
                    403,
                )
            return view(*args, **kwargs)

        return wrapped

    return decorator
