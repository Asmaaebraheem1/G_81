"""Server-rendered Jinja admin panel. Cookie session + CSRF only."""

from __future__ import annotations

import csv
import io
import secrets
from datetime import date, datetime, time, timedelta
from pathlib import Path

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from sqlalchemy import func, or_
from werkzeug.security import check_password_hash, generate_password_hash

from app.core.db import db, utcnow
from app.core.errors import ApiError
from app.core.periods import demo_today, month_starts, parse_iso_date
from app.core.rate_limit import login_limiter
from app.core.security import current_admin_id, current_admin_role, role_required
from app.core.text import redact_pii
from app.core.validators import clean_email
from app.modules.admin.forms import (
    AdminForm,
    AppSettingForm,
    ArticleForm,
    BadgeForm,
    CategoryForm,
    ChallengeForm,
    FactorForm,
    FlagResolveForm,
    LoginForm,
    NotificationForm,
    SettingsForm,
)
from app.modules.admin.models import Admin, AdminAuditLog, AppSetting
from app.modules.admin.service import admin_ip, current_admin, login_admin, record
from app.modules.ai.models import AiFlaggedResponse, AiUsage
from app.modules.ai.service import DISCLAIMER
from app.modules.catalog.models import EmissionCategory, EmissionFactor
from app.modules.challenges.models import Badge, Challenge
from app.modules.content.models import Article
from app.modules.documents.models import Document
from app.modules.goals.models import Goal
from app.modules.notifications.models import Notification
from app.modules.notifications.service import create_notification
from app.modules.organizations.models import Organization
from app.modules.plans.models import ReductionPlan
from app.modules.records.models import ConsumptionRecord
from app.modules.users.models import RefreshToken, User

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
def _require_login():
    if request.endpoint == "admin.login":
        return None
    if current_admin_id() is None:
        return redirect(url_for("admin.login", next=request.path))
    admin = current_admin()
    if admin is None or not admin.is_active:
        session.clear()
        flash("Your admin session is no longer valid.", "error")
        return redirect(url_for("admin.login"))
    return None


@admin_bp.context_processor
def _inject_admin():
    return {
        "current_admin": current_admin(),
        "current_role": current_admin_role(),
        "today": demo_today(),
        "open_flags": AiFlaggedResponse.query.filter_by(status="open").count(),
    }


@admin_bp.app_template_filter("fmt_dt")
def _fmt_dt(value):
    if not value:
        return "—"
    return value.strftime("%Y-%m-%d %H:%M")


@admin_bp.app_template_filter("fmt_date")
def _fmt_date(value):
    if not value:
        return "—"
    return value.strftime("%Y-%m-%d")


@admin_bp.app_template_filter("kg")
def _kg(value):
    return f"{(value or 0) / 1000:,.2f}"


@admin_bp.app_template_filter("redact")
def _redact(value):
    return redact_pii(str(value or ""))


def _page(query, per_page: int = 20):
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1
    return query.paginate(page=page, per_page=per_page, error_out=False)


def _q() -> str:
    return (request.args.get("q") or "").strip()


# ---------------------------------------------------------------- auth


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_admin_id() is not None:
        return redirect(url_for("admin.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        email = (form.email.data or "").strip().lower()
        key = f"admin:{admin_ip()}:{email}"
        try:
            login_limiter.check(key)
        except ApiError as exc:
            flash(exc.message, "error")
            return render_template("admin/login.html", form=form), 429
        admin = Admin.query.filter_by(email=email).first()
        if (
            admin is None
            or not admin.is_active
            or not check_password_hash(admin.password_hash, form.password.data)
        ):
            flash("Invalid email or password.", "error")
            return render_template("admin/login.html", form=form), 401
        login_limiter.reset(key)
        login_admin(admin)
        record("login", "admin", admin.id)
        next_url = request.args.get("next")
        if next_url and next_url.startswith("/admin"):
            return redirect(next_url)
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/login.html", form=form)


@admin_bp.post("/logout")
def logout():
    record("logout", "admin", current_admin_id())
    session.clear()
    flash("Signed out.", "success")
    return redirect(url_for("admin.login"))


# ---------------------------------------------------------------- dashboard


@admin_bp.get("/")
def dashboard():
    month_start = demo_today().replace(day=1)
    month_end = demo_today()
    totals = (
        db.session.query(func.coalesce(func.sum(ConsumptionRecord.emissions_grams), 0))
        .filter(
            ConsumptionRecord.status == "active",
            ConsumptionRecord.activity_date.between(month_start, month_end),
        )
        .scalar()
    )
    categories = (
        db.session.query(
            EmissionCategory.name_en,
            EmissionCategory.name_ar,
            EmissionCategory.color_hex,
            func.sum(ConsumptionRecord.emissions_grams).label("grams"),
        )
        .join(ConsumptionRecord, ConsumptionRecord.category_id == EmissionCategory.id)
        .filter(
            ConsumptionRecord.status == "active",
            ConsumptionRecord.activity_date.between(month_start, month_end),
        )
        .group_by(EmissionCategory.id)
        .order_by(func.sum(ConsumptionRecord.emissions_grams).desc())
        .all()
    )
    total_grams = int(totals or 0)
    category_rows = [
        {
            "name": row.name_en,
            "name_ar": row.name_ar,
            "color": row.color_hex or "#2f8f6b",
            "grams": int(row.grams or 0),
            "share": round(int(row.grams or 0) / total_grams * 100, 1) if total_grams else 0,
        }
        for row in categories
    ]
    stats = {
        "users": User.query.count(),
        "active_users": User.query.filter_by(is_active=True).count(),
        "organizations": Organization.query.count(),
        "records": ConsumptionRecord.query.filter_by(status="active").count(),
        "month_grams": total_grams,
        "goals": Goal.query.filter_by(status="active").count(),
        "plans": ReductionPlan.query.count(),
        "documents": Document.query.count(),
        "open_flags": AiFlaggedResponse.query.filter_by(status="open").count(),
        "ai_calls_7d": AiUsage.query.filter(
            AiUsage.created_at >= utcnow() - timedelta(days=7)
        ).count(),
    }
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_audit = AdminAuditLog.query.order_by(AdminAuditLog.created_at.desc()).limit(8).all()
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        categories=category_rows,
        recent_users=recent_users,
        recent_audit=recent_audit,
    )


# ---------------------------------------------------------------- users


@admin_bp.get("/users")
@role_required("super_admin")
def users():
    query = User.query
    q = _q()
    if q:
        like = f"%{q}%"
        query = query.filter(or_(User.email.ilike(like), User.full_name.ilike(like)))
    status = request.args.get("status")
    if status == "active":
        query = query.filter_by(is_active=True)
    elif status == "suspended":
        query = query.filter_by(is_active=False)
    pagination = _page(query.order_by(User.created_at.desc()))
    return render_template("admin/users.html", pagination=pagination, q=q, status=status)


@admin_bp.get("/users/<int:user_id>")
@role_required("super_admin")
def user_detail(user_id: int):
    user = db.session.get(User, user_id)
    if user is None:
        flash("User not found.", "error")
        return redirect(url_for("admin.users"))
    records = (
        ConsumptionRecord.query.filter_by(user_id=user.id)
        .order_by(ConsumptionRecord.activity_date.desc())
        .limit(10)
        .all()
    )
    return render_template(
        "admin/user_detail.html",
        user=user,
        records=records,
        record_count=ConsumptionRecord.query.filter_by(user_id=user.id, status="active").count(),
        goal_count=Goal.query.filter_by(user_id=user.id).count(),
        plan_count=ReductionPlan.query.filter_by(user_id=user.id).count(),
        document_count=Document.query.filter_by(user_id=user.id).count(),
    )


@admin_bp.post("/users/<int:user_id>/action")
@role_required("super_admin")
def user_action(user_id: int):
    user = db.session.get(User, user_id)
    if user is None:
        flash("User not found.", "error")
        return redirect(url_for("admin.users"))
    action = request.form.get("action")
    if action == "activate":
        user.is_active = True
        record("activate", "user", user.id, {"email": user.email})
        flash("User activated.", "success")
    elif action == "suspend":
        user.is_active = False
        RefreshToken.query.filter_by(user_id=user.id, revoked_at=None).update(
            {"revoked_at": utcnow()}
        )
        record("suspend", "user", user.id, {"email": user.email})
        flash("User suspended and sessions revoked.", "success")
    elif action == "reset-password":
        temp = f"Temp-{secrets.token_urlsafe(6)}A1!"
        user.password_hash = generate_password_hash(temp)
        RefreshToken.query.filter_by(user_id=user.id, revoked_at=None).update(
            {"revoked_at": utcnow()}
        )
        db.session.commit()
        record("reset_password", "user", user.id, {"email": user.email})
        flash(f"Temporary password (demo only): {temp}", "success")
        return redirect(url_for("admin.user_detail", user_id=user.id))
    else:
        flash("Unknown action.", "error")
    db.session.commit()
    return redirect(request.referrer or url_for("admin.users"))


# ---------------------------------------------------------------- organizations


@admin_bp.get("/organizations")
@role_required("super_admin")
def organizations():
    query = Organization.query
    q = _q()
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(Organization.name_en.ilike(like), Organization.name_ar.ilike(like))
        )
    pagination = _page(query.order_by(Organization.created_at.desc()))
    return render_template("admin/organizations.html", pagination=pagination, q=q)


@admin_bp.get("/organizations/<int:org_id>")
@role_required("super_admin")
def organization_detail(org_id: int):
    org = db.session.get(Organization, org_id)
    if org is None:
        flash("Organization not found.", "error")
        return redirect(url_for("admin.organizations"))
    return render_template(
        "admin/organization_detail.html",
        org=org,
        users=User.query.filter_by(organization_id=org.id).all(),
        record_count=ConsumptionRecord.query.filter_by(
            organization_id=org.id, status="active"
        ).count(),
        goal_count=Goal.query.filter_by(organization_id=org.id).count(),
    )


@admin_bp.post("/organizations/<int:org_id>/action")
@role_required("super_admin")
def organization_action(org_id: int):
    org = db.session.get(Organization, org_id)
    if org is None:
        flash("Organization not found.", "error")
        return redirect(url_for("admin.organizations"))
    action = request.form.get("action")
    if action == "verify":
        org.is_verified = True
    elif action == "unverify":
        org.is_verified = False
    elif action == "activate":
        org.is_active = True
    elif action == "suspend":
        org.is_active = False
    else:
        flash("Unknown action.", "error")
        return redirect(request.referrer or url_for("admin.organizations"))
    db.session.commit()
    record(action, "organization", org.id, {"name": org.name_en})
    flash("Organization updated.", "success")
    return redirect(request.referrer or url_for("admin.organizations"))


# ---------------------------------------------------------------- categories


@admin_bp.get("/categories")
def categories():
    rows = EmissionCategory.query.order_by(
        EmissionCategory.sort_order, EmissionCategory.name_en
    ).all()
    return render_template("admin/categories.html", categories=rows)


@admin_bp.route("/categories/new", methods=["GET", "POST"])
def category_new():
    form = CategoryForm()
    if form.validate_on_submit():
        if EmissionCategory.query.filter_by(key=form.key.data.strip()).first():
            flash("That key already exists.", "error")
        else:
            row = EmissionCategory(
                key=form.key.data.strip(),
                name_en=form.name_en.data.strip(),
                name_ar=form.name_ar.data.strip(),
                description_en=form.description_en.data,
                description_ar=form.description_ar.data,
                icon=form.icon.data,
                color_hex=form.color_hex.data,
                unit_hint=form.unit_hint.data,
                sort_order=form.sort_order.data or 0,
                is_active=form.is_active.data,
            )
            db.session.add(row)
            db.session.commit()
            record("create", "category", row.id, {"key": row.key})
            flash("Category created.", "success")
            return redirect(url_for("admin.categories"))
    return render_template("admin/category_form.html", form=form, mode="new")


@admin_bp.route("/categories/<int:category_id>/edit", methods=["GET", "POST"])
def category_edit(category_id: int):
    row = db.session.get(EmissionCategory, category_id)
    if row is None:
        flash("Category not found.", "error")
        return redirect(url_for("admin.categories"))
    form = CategoryForm(obj=row)
    if form.validate_on_submit():
        duplicate = EmissionCategory.query.filter(
            EmissionCategory.key == form.key.data.strip(),
            EmissionCategory.id != row.id,
        ).first()
        if duplicate:
            flash("That key already exists.", "error")
        else:
            for field in (
                "key",
                "name_en",
                "name_ar",
                "description_en",
                "description_ar",
                "icon",
                "color_hex",
                "unit_hint",
                "sort_order",
                "is_active",
            ):
                setattr(row, field, getattr(form, field).data)
            db.session.commit()
            record("update", "category", row.id, {"key": row.key})
            flash("Category updated.", "success")
            return redirect(url_for("admin.categories"))
    return render_template("admin/category_form.html", form=form, mode="edit", row=row)


@admin_bp.post("/categories/<int:category_id>/toggle")
def category_toggle(category_id: int):
    row = db.session.get(EmissionCategory, category_id)
    if row is None:
        flash("Category not found.", "error")
        return redirect(url_for("admin.categories"))
    row.is_active = not row.is_active
    db.session.commit()
    record("toggle", "category", row.id, {"active": row.is_active})
    flash("Category updated.", "success")
    return redirect(url_for("admin.categories"))


# ---------------------------------------------------------------- factors


@admin_bp.get("/factors")
def factors():
    query = EmissionFactor.query
    q = _q()
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(EmissionFactor.name_en.ilike(like), EmissionFactor.key.ilike(like))
        )
    category_id = request.args.get("category_id", type=int)
    if category_id:
        query = query.filter_by(category_id=category_id)
    pagination = _page(query.order_by(EmissionFactor.category_id, EmissionFactor.name_en), 30)
    return render_template(
        "admin/factors.html",
        pagination=pagination,
        q=q,
        category_id=category_id,
        categories=EmissionCategory.query.order_by(EmissionCategory.sort_order).all(),
    )


def _factor_form_choices(form: FactorForm) -> None:
    form.category_id.choices = [
        (row.id, row.name_en)
        for row in EmissionCategory.query.order_by(EmissionCategory.sort_order).all()
    ]


@admin_bp.route("/factors/new", methods=["GET", "POST"])
def factor_new():
    form = FactorForm()
    _factor_form_choices(form)
    if form.validate_on_submit():
        if form.valid_to.data and form.valid_to.data < form.valid_from.data:
            flash("Valid-to date must be after valid-from date.", "error")
        elif EmissionFactor.query.filter_by(key=form.key.data.strip()).first():
            flash("That key already exists.", "error")
        else:
            row = EmissionFactor(
                category_id=form.category_id.data,
                key=form.key.data.strip(),
                name_en=form.name_en.data.strip(),
                name_ar=form.name_ar.data.strip(),
                activity_type=form.activity_type.data.strip(),
                unit=form.unit.data.strip(),
                factor_grams_co2e=form.factor_grams_co2e.data,
                source_name=form.source_name.data.strip(),
                source_url=form.source_url.data,
                source_year=form.source_year.data,
                region=form.region.data.strip(),
                valid_from=form.valid_from.data,
                valid_to=form.valid_to.data,
                is_active=form.is_active.data,
                notes=form.notes.data,
            )
            db.session.add(row)
            db.session.commit()
            record("create", "factor", row.id, {"key": row.key})
            flash("Factor created.", "success")
            return redirect(url_for("admin.factors"))
    return render_template("admin/factor_form.html", form=form, mode="new")


@admin_bp.route("/factors/<int:factor_id>/edit", methods=["GET", "POST"])
def factor_edit(factor_id: int):
    row = db.session.get(EmissionFactor, factor_id)
    if row is None:
        flash("Factor not found.", "error")
        return redirect(url_for("admin.factors"))
    form = FactorForm(obj=row)
    _factor_form_choices(form)
    if form.validate_on_submit():
        if form.valid_to.data and form.valid_to.data < form.valid_from.data:
            flash("Valid-to date must be after valid-from date.", "error")
        else:
            for field in (
                "category_id",
                "key",
                "name_en",
                "name_ar",
                "activity_type",
                "unit",
                "factor_grams_co2e",
                "source_name",
                "source_url",
                "source_year",
                "region",
                "valid_from",
                "valid_to",
                "is_active",
                "notes",
            ):
                setattr(row, field, getattr(form, field).data)
            db.session.commit()
            record("update", "factor", row.id, {"key": row.key})
            flash("Factor updated. Existing records keep their factor snapshots.", "success")
            return redirect(url_for("admin.factors"))
    return render_template("admin/factor_form.html", form=form, mode="edit", row=row)


@admin_bp.post("/factors/<int:factor_id>/toggle")
def factor_toggle(factor_id: int):
    row = db.session.get(EmissionFactor, factor_id)
    if row is None:
        flash("Factor not found.", "error")
        return redirect(url_for("admin.factors"))
    row.is_active = not row.is_active
    db.session.commit()
    record("toggle", "factor", row.id, {"active": row.is_active})
    flash("Factor updated.", "success")
    return redirect(url_for("admin.factors"))


# ---------------------------------------------------------------- records


@admin_bp.get("/records")
def records():
    query = ConsumptionRecord.query
    q = _q()
    if q:
        like = f"%{q}%"
        query = query.join(EmissionCategory).filter(
            or_(
                ConsumptionRecord.notes.ilike(like),
                EmissionCategory.name_en.ilike(like),
                EmissionCategory.name_ar.ilike(like),
            )
        )
    status = request.args.get("status")
    if status:
        query = query.filter(ConsumptionRecord.status == status)
    category_id = request.args.get("category_id", type=int)
    if category_id:
        query = query.filter(ConsumptionRecord.category_id == category_id)
    pagination = _page(
        query.order_by(ConsumptionRecord.activity_date.desc(), ConsumptionRecord.id.desc()),
        30,
    )
    return render_template(
        "admin/records.html",
        pagination=pagination,
        q=q,
        status=status,
        category_id=category_id,
        categories=EmissionCategory.query.order_by(EmissionCategory.sort_order).all(),
    )


@admin_bp.get("/records/<int:record_id>")
def record_detail(record_id: int):
    row = db.session.get(ConsumptionRecord, record_id)
    if row is None:
        flash("Record not found.", "error")
        return redirect(url_for("admin.records"))
    return render_template("admin/record_detail.html", record=row)


@admin_bp.post("/records/<int:record_id>/status")
@role_required("super_admin")
def record_status(record_id: int):
    row = db.session.get(ConsumptionRecord, record_id)
    if row is None:
        flash("Record not found.", "error")
        return redirect(url_for("admin.records"))
    status = request.form.get("status")
    if status not in {"active", "flagged", "deleted"}:
        flash("Invalid status.", "error")
    else:
        row.status = status
        db.session.commit()
        record("update_status", "record", row.id, {"status": status})
        flash("Record status updated.", "success")
    return redirect(request.referrer or url_for("admin.records"))


# ---------------------------------------------------------------- documents


@admin_bp.get("/documents")
@role_required("super_admin")
def documents():
    query = Document.query
    q = _q()
    if q:
        like = f"%{q}%"
        query = query.filter(Document.original_filename.ilike(like))
    pagination = _page(query.order_by(Document.created_at.desc()), 30)
    return render_template("admin/documents.html", pagination=pagination, q=q)


@admin_bp.get("/documents/<int:document_id>")
@role_required("super_admin")
def document_detail(document_id: int):
    row = db.session.get(Document, document_id)
    if row is None:
        flash("Document not found.", "error")
        return redirect(url_for("admin.documents"))
    return render_template("admin/document_detail.html", document=row)


@admin_bp.get("/documents/<int:document_id>/download")
@role_required("super_admin")
def document_download(document_id: int):
    row = db.session.get(Document, document_id)
    if row is None:
        flash("Document not found.", "error")
        return redirect(url_for("admin.documents"))
    from flask import current_app

    root = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    path = (root / row.storage_path).resolve()
    if root not in path.parents or not path.exists():
        flash("Stored file missing.", "error")
        return redirect(url_for("admin.document_detail", document_id=row.id))
    record("download", "document", row.id, {"filename": row.original_filename})
    return send_file(
        path,
        mimetype=row.mime_type,
        as_attachment=True,
        download_name=row.original_filename,
    )


@admin_bp.post("/documents/<int:document_id>/delete")
@role_required("super_admin")
def document_delete(document_id: int):
    row = db.session.get(Document, document_id)
    if row is None:
        flash("Document not found.", "error")
        return redirect(url_for("admin.documents"))
    if row.record_id is not None:
        flash("Delete the linked record first.", "error")
        return redirect(url_for("admin.document_detail", document_id=row.id))
    from flask import current_app

    root = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    path = (root / row.storage_path).resolve()
    if root in path.parents and path.exists():
        try:
            path.unlink()
        except OSError:
            pass
    db.session.delete(row)
    db.session.commit()
    record("delete", "document", document_id, {})
    flash("Document deleted.", "success")
    return redirect(url_for("admin.documents"))


# ---------------------------------------------------------------- plans & goals


@admin_bp.get("/plans")
@role_required("super_admin")
def plans():
    query = ReductionPlan.query
    q = _q()
    if q:
        query = query.filter(ReductionPlan.title.ilike(f"%{q}%"))
    pagination = _page(query.order_by(ReductionPlan.created_at.desc()))
    return render_template("admin/plans.html", pagination=pagination, q=q)


@admin_bp.get("/plans/<int:plan_id>")
@role_required("super_admin")
def plan_detail(plan_id: int):
    plan = db.session.get(ReductionPlan, plan_id)
    if plan is None:
        flash("Plan not found.", "error")
        return redirect(url_for("admin.plans"))
    return render_template("admin/plan_detail.html", plan=plan)


@admin_bp.post("/plans/<int:plan_id>/status")
@role_required("super_admin")
def plan_status(plan_id: int):
    plan = db.session.get(ReductionPlan, plan_id)
    if plan is None:
        flash("Plan not found.", "error")
        return redirect(url_for("admin.plans"))
    status = request.form.get("status")
    if status in {"draft", "active", "completed", "archived"}:
        plan.status = status
        db.session.commit()
        record("update_status", "plan", plan.id, {"status": status})
        flash("Plan status updated.", "success")
    return redirect(url_for("admin.plan_detail", plan_id=plan.id))


@admin_bp.get("/goals")
@role_required("super_admin")
def goals():
    query = Goal.query
    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)
    pagination = _page(query.order_by(Goal.created_at.desc()))
    return render_template("admin/goals.html", pagination=pagination, status=status)


@admin_bp.get("/goals/<int:goal_id>")
@role_required("super_admin")
def goal_detail(goal_id: int):
    goal = db.session.get(Goal, goal_id)
    if goal is None:
        flash("Goal not found.", "error")
        return redirect(url_for("admin.goals"))
    return render_template("admin/goal_detail.html", goal=goal)


# ---------------------------------------------------------------- reports


def _global_report_bounds():
    start = parse_iso_date(request.args.get("from")) or demo_today().replace(day=1)
    end = parse_iso_date(request.args.get("to")) or demo_today()
    if start > end:
        start, end = end, start
    return start, end


@admin_bp.get("/reports")
@role_required("super_admin")
def reports():
    start, end = _global_report_bounds()
    base = ConsumptionRecord.query.filter(
        ConsumptionRecord.status == "active",
        ConsumptionRecord.activity_date.between(start, end),
    )
    total = int(
        base.with_entities(func.coalesce(func.sum(ConsumptionRecord.emissions_grams), 0)).scalar()
        or 0
    )
    categories = (
        base.join(EmissionCategory, ConsumptionRecord.category_id == EmissionCategory.id)
        .with_entities(
            EmissionCategory.name_en,
            EmissionCategory.name_ar,
            EmissionCategory.color_hex,
            func.sum(ConsumptionRecord.emissions_grams).label("grams"),
        )
        .group_by(EmissionCategory.id)
        .order_by(func.sum(ConsumptionRecord.emissions_grams).desc())
        .all()
    )
    category_rows = [
        {
            "name": row.name_en,
            "name_ar": row.name_ar,
            "color": row.color_hex or "#2f8f6b",
            "grams": int(row.grams or 0),
            "share": round(int(row.grams or 0) / total * 100, 1) if total else 0,
        }
        for row in categories
    ]
    monthly = []
    for month_start in month_starts(6, end):
        if month_start.month == 12:
            month_end = date(month_start.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(month_start.year, month_start.month + 1, 1) - timedelta(days=1)
        grams = int(
            ConsumptionRecord.query.filter(
                ConsumptionRecord.status == "active",
                ConsumptionRecord.activity_date.between(month_start, month_end),
            )
            .with_entities(func.coalesce(func.sum(ConsumptionRecord.emissions_grams), 0))
            .scalar()
            or 0
        )
        monthly.append({"label": month_start.strftime("%b %Y"), "grams": grams})
    top = (
        base.join(EmissionFactor, ConsumptionRecord.factor_id == EmissionFactor.id)
        .with_entities(
            EmissionFactor.name_en,
            EmissionFactor.name_ar,
            EmissionFactor.unit,
            func.sum(ConsumptionRecord.emissions_grams).label("grams"),
            func.count(ConsumptionRecord.id).label("records"),
        )
        .group_by(EmissionFactor.id)
        .order_by(func.sum(ConsumptionRecord.emissions_grams).desc())
        .limit(8)
        .all()
    )
    return render_template(
        "admin/reports.html",
        start=start,
        end=end,
        total=total,
        categories=category_rows,
        monthly=monthly,
        top=top,
        user_count=base.with_entities(ConsumptionRecord.user_id).distinct().count(),
    )


@admin_bp.get("/reports/export.csv")
@role_required("super_admin")
def reports_export():
    start, end = _global_report_bounds()
    rows = (
        ConsumptionRecord.query.join(User, ConsumptionRecord.user_id == User.id)
        .filter(
            ConsumptionRecord.status == "active",
            ConsumptionRecord.activity_date.between(start, end),
        )
        .order_by(ConsumptionRecord.activity_date)
        .all()
    )
    buffer = io.StringIO()
    buffer.write("\ufeff")
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "record_id",
            "user_email",
            "activity_date",
            "category",
            "quantity",
            "unit",
            "factor_grams",
            "emissions_grams",
            "emissions_kg",
            "source",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row.id,
                row.user.email if row.user else "",
                row.activity_date.isoformat(),
                row.category.name_en if row.category else "",
                float(row.quantity),
                row.unit,
                row.factor_grams_co2e_snapshot,
                row.emissions_grams,
                f"{row.emissions_kg:.2f}",
                row.source,
            ]
        )
    record("export", "report", None, {"from": start.isoformat(), "to": end.isoformat()})
    return send_file(
        io.BytesIO(buffer.getvalue().encode("utf-8")),
        mimetype="text/csv; charset=utf-8",
        as_attachment=True,
        download_name=f"carbonwise-admin-{start}-{end}.csv",
    )


# ---------------------------------------------------------------- challenges


@admin_bp.get("/challenges")
def challenges():
    rows = Challenge.query.order_by(Challenge.start_date.desc()).all()
    return render_template("admin/challenges.html", challenges=rows)


def _challenge_choices(form: ChallengeForm) -> None:
    form.category_id.choices = [(0, "— none —")] + [
        (row.id, row.name_en)
        for row in EmissionCategory.query.order_by(EmissionCategory.sort_order).all()
    ]
    form.badge_id.choices = [(0, "— none —")] + [
        (row.id, row.title_en) for row in Badge.query.order_by(Badge.title_en).all()
    ]


@admin_bp.route("/challenges/new", methods=["GET", "POST"])
def challenge_new():
    form = ChallengeForm()
    _challenge_choices(form)
    if form.validate_on_submit():
        if form.end_date.data < form.start_date.data:
            flash("End date must be after start date.", "error")
        elif Challenge.query.filter_by(key=form.key.data.strip()).first():
            flash("That key already exists.", "error")
        else:
            row = Challenge(
                key=form.key.data.strip(),
                title_en=form.title_en.data.strip(),
                title_ar=form.title_ar.data.strip(),
                description_en=form.description_en.data,
                description_ar=form.description_ar.data,
                type=form.type.data,
                category_id=form.category_id.data or None,
                target_type=form.target_type.data,
                target_value=form.target_value.data,
                points=form.points.data or 0,
                badge_id=form.badge_id.data or None,
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                is_active=form.is_active.data,
            )
            db.session.add(row)
            db.session.commit()
            record("create", "challenge", row.id, {"key": row.key})
            flash("Challenge created.", "success")
            return redirect(url_for("admin.challenges"))
    return render_template("admin/challenge_form.html", form=form, mode="new")


@admin_bp.route("/challenges/<int:challenge_id>/edit", methods=["GET", "POST"])
def challenge_edit(challenge_id: int):
    row = db.session.get(Challenge, challenge_id)
    if row is None:
        flash("Challenge not found.", "error")
        return redirect(url_for("admin.challenges"))
    form = ChallengeForm(obj=row)
    _challenge_choices(form)
    if request.method == "GET":
        form.category_id.data = row.category_id or 0
        form.badge_id.data = row.badge_id or 0
    if form.validate_on_submit():
        if form.end_date.data < form.start_date.data:
            flash("End date must be after start date.", "error")
        else:
            for field in (
                "key",
                "title_en",
                "title_ar",
                "description_en",
                "description_ar",
                "type",
                "target_type",
                "target_value",
                "points",
                "start_date",
                "end_date",
                "is_active",
            ):
                setattr(row, field, getattr(form, field).data)
            row.category_id = form.category_id.data or None
            row.badge_id = form.badge_id.data or None
            db.session.commit()
            record("update", "challenge", row.id, {"key": row.key})
            flash("Challenge updated.", "success")
            return redirect(url_for("admin.challenges"))
    return render_template("admin/challenge_form.html", form=form, mode="edit", row=row)


@admin_bp.post("/challenges/<int:challenge_id>/toggle")
def challenge_toggle(challenge_id: int):
    row = db.session.get(Challenge, challenge_id)
    if row is None:
        flash("Challenge not found.", "error")
        return redirect(url_for("admin.challenges"))
    row.is_active = not row.is_active
    db.session.commit()
    record("toggle", "challenge", row.id, {"active": row.is_active})
    flash("Challenge updated.", "success")
    return redirect(url_for("admin.challenges"))


# ---------------------------------------------------------------- badges


@admin_bp.get("/badges")
def badges():
    rows = Badge.query.order_by(Badge.title_en).all()
    return render_template("admin/badges.html", badges=rows)


@admin_bp.route("/badges/new", methods=["GET", "POST"])
def badge_new():
    form = BadgeForm()
    if form.validate_on_submit():
        if Badge.query.filter_by(key=form.key.data.strip()).first():
            flash("That key already exists.", "error")
        else:
            row = Badge(
                key=form.key.data.strip(),
                title_en=form.title_en.data.strip(),
                title_ar=form.title_ar.data.strip(),
                description_en=form.description_en.data,
                description_ar=form.description_ar.data,
                icon=form.icon.data,
                criteria=form.criteria.data,
                points=form.points.data or 0,
            )
            db.session.add(row)
            db.session.commit()
            record("create", "badge", row.id, {"key": row.key})
            flash("Badge created.", "success")
            return redirect(url_for("admin.badges"))
    return render_template("admin/badge_form.html", form=form, mode="new")


@admin_bp.route("/badges/<int:badge_id>/edit", methods=["GET", "POST"])
def badge_edit(badge_id: int):
    row = db.session.get(Badge, badge_id)
    if row is None:
        flash("Badge not found.", "error")
        return redirect(url_for("admin.badges"))
    form = BadgeForm(obj=row)
    if form.validate_on_submit():
        for field in (
            "key",
            "title_en",
            "title_ar",
            "description_en",
            "description_ar",
            "icon",
            "criteria",
            "points",
        ):
            setattr(row, field, getattr(form, field).data)
        db.session.commit()
        record("update", "badge", row.id, {"key": row.key})
        flash("Badge updated.", "success")
        return redirect(url_for("admin.badges"))
    return render_template("admin/badge_form.html", form=form, mode="edit", row=row)


# ---------------------------------------------------------------- notifications


@admin_bp.get("/notifications")
def notifications():
    rows = Notification.query.order_by(Notification.created_at.desc()).limit(200).all()
    return render_template("admin/notifications.html", notifications=rows)


@admin_bp.route("/notifications/new", methods=["GET", "POST"])
def notification_new():
    form = NotificationForm()
    if form.validate_on_submit():
        target_id = None
        if form.target.data == "email":
            email = (form.email.data or "").strip().lower()
            user = User.query.filter_by(email=email).first() if email else None
            if user is None:
                flash("No user found with that email.", "error")
                return render_template("admin/notification_form.html", form=form)
            target_id = user.id
        create_notification(
            target_id,
            form.type.data,
            form.title_en.data.strip(),
            form.title_ar.data.strip(),
            form.body_en.data,
            form.body_ar.data,
            form.action_url.data,
        )
        record("create", "notification", None, {"target": form.target.data, "type": form.type.data})
        flash("Notification sent.", "success")
        return redirect(url_for("admin.notifications"))
    return render_template("admin/notification_form.html", form=form)


# ---------------------------------------------------------------- AI monitor


@admin_bp.get("/ai")
def ai_monitor():
    stats = {
        "calls": AiUsage.query.count(),
        "today_tokens": int(
            db.session.query(func.coalesce(func.sum(AiUsage.total_tokens), 0))
            .filter(AiUsage.created_at >= datetime.combine(demo_today(), time.min))
            .scalar()
            or 0
        ),
        "errors": AiUsage.query.filter(AiUsage.status != "success").count(),
        "open_flags": AiFlaggedResponse.query.filter_by(status="open").count(),
    }
    usage = _page(AiUsage.query.order_by(AiUsage.created_at.desc()), 30)
    flags = AiFlaggedResponse.query.order_by(AiFlaggedResponse.created_at.desc()).limit(50).all()
    return render_template(
        "admin/ai.html",
        stats=stats,
        usage=usage,
        flags=flags,
        resolve_form=FlagResolveForm(),
        disclaimer=DISCLAIMER,
    )


@admin_bp.post("/ai/flags/<int:flag_id>/resolve")
def ai_flag_resolve(flag_id: int):
    row = db.session.get(AiFlaggedResponse, flag_id)
    if row is None:
        flash("Flag not found.", "error")
        return redirect(url_for("admin.ai_monitor"))
    form = FlagResolveForm()
    if form.validate_on_submit():
        row.status = form.status.data
        row.admin_notes = redact_pii(form.admin_notes.data or "")[:2000]
        row.resolved_at = utcnow()
        db.session.commit()
        record("resolve", "ai_flag", row.id, {"status": row.status})
        flash("Flag resolved.", "success")
    return redirect(url_for("admin.ai_monitor"))


# ---------------------------------------------------------------- content


@admin_bp.get("/content")
def content():
    rows = Article.query.order_by(Article.sort_order, Article.published_at.desc()).all()
    return render_template("admin/content.html", articles=rows)


@admin_bp.route("/content/new", methods=["GET", "POST"])
def content_new():
    form = ArticleForm()
    if form.validate_on_submit():
        if Article.query.filter_by(slug=form.slug.data.strip()).first():
            flash("That slug already exists.", "error")
        else:
            row = Article(
                slug=form.slug.data.strip(),
                title_en=form.title_en.data.strip(),
                title_ar=form.title_ar.data.strip(),
                summary_en=form.summary_en.data,
                summary_ar=form.summary_ar.data,
                body_en=form.body_en.data,
                body_ar=form.body_ar.data,
                image_path=form.image_path.data,
                category=form.category.data,
                is_published=form.is_published.data,
                published_at=utcnow() if form.is_published.data else None,
                sort_order=form.sort_order.data or 0,
            )
            db.session.add(row)
            db.session.commit()
            record("create", "article", row.id, {"slug": row.slug})
            flash("Article created.", "success")
            return redirect(url_for("admin.content"))
    return render_template("admin/article_form.html", form=form, mode="new")


@admin_bp.route("/content/<int:article_id>/edit", methods=["GET", "POST"])
def content_edit(article_id: int):
    row = db.session.get(Article, article_id)
    if row is None:
        flash("Article not found.", "error")
        return redirect(url_for("admin.content"))
    form = ArticleForm(obj=row)
    if form.validate_on_submit():
        for field in (
            "slug",
            "title_en",
            "title_ar",
            "summary_en",
            "summary_ar",
            "body_en",
            "body_ar",
            "image_path",
            "category",
            "is_published",
            "sort_order",
        ):
            setattr(row, field, getattr(form, field).data)
        if row.is_published and row.published_at is None:
            row.published_at = utcnow()
        db.session.commit()
        record("update", "article", row.id, {"slug": row.slug})
        flash("Article updated.", "success")
        return redirect(url_for("admin.content"))
    return render_template("admin/article_form.html", form=form, mode="edit", row=row)


@admin_bp.post("/content/<int:article_id>/toggle")
def content_toggle(article_id: int):
    row = db.session.get(Article, article_id)
    if row is None:
        flash("Article not found.", "error")
        return redirect(url_for("admin.content"))
    row.is_published = not row.is_published
    if row.is_published and row.published_at is None:
        row.published_at = utcnow()
    db.session.commit()
    record("toggle", "article", row.id, {"published": row.is_published})
    flash("Article updated.", "success")
    return redirect(url_for("admin.content"))


@admin_bp.post("/content/<int:article_id>/delete")
def content_delete(article_id: int):
    row = db.session.get(Article, article_id)
    if row is None:
        flash("Article not found.", "error")
        return redirect(url_for("admin.content"))
    db.session.delete(row)
    db.session.commit()
    record("delete", "article", article_id, {})
    flash("Article deleted.", "success")
    return redirect(url_for("admin.content"))


# ---------------------------------------------------------------- settings


@admin_bp.route("/settings", methods=["GET", "POST"])
def settings():
    admin = current_admin()
    form = SettingsForm(obj=admin)
    if form.validate_on_submit():
        email = clean_email(form.email.data)
        duplicate = Admin.query.filter(Admin.email == email, Admin.id != admin.id).first()
        if duplicate:
            flash("That email is already used by another admin.", "error")
        else:
            admin.name = form.name.data.strip()
            admin.email = email
            if form.password.data:
                admin.password_hash = generate_password_hash(form.password.data)
            db.session.commit()
            session["admin_name"] = admin.name
            record("update", "admin", admin.id, {"email": admin.email})
            flash("Profile updated.", "success")
            return redirect(url_for("admin.settings"))
    admins = Admin.query.order_by(Admin.created_at).all()
    admin_form = AdminForm()
    setting_form = AppSettingForm()
    settings_rows = AppSetting.query.order_by(AppSetting.key).all()
    return render_template(
        "admin/settings.html",
        form=form,
        admin_form=admin_form,
        setting_form=setting_form,
        admins=admins,
        settings_rows=settings_rows,
    )


@admin_bp.post("/settings/admins")
@role_required("super_admin")
def create_admin():
    form = AdminForm()
    if form.validate_on_submit():
        email = clean_email(form.email.data)
        if Admin.query.filter_by(email=email).first():
            flash("That admin email already exists.", "error")
        else:
            row = Admin(
                email=email,
                name=form.name.data.strip(),
                role=form.role.data,
                password_hash=generate_password_hash(form.password.data),
                is_active=True,
            )
            db.session.add(row)
            db.session.commit()
            record("create", "admin", row.id, {"email": row.email, "role": row.role})
            flash("Admin created.", "success")
    else:
        flash("Please complete every admin field.", "error")
    return redirect(url_for("admin.settings"))


@admin_bp.post("/settings/admins/<int:admin_id>/toggle")
@role_required("super_admin")
def toggle_admin(admin_id: int):
    admin = db.session.get(Admin, admin_id)
    if admin is None:
        flash("Admin not found.", "error")
        return redirect(url_for("admin.settings"))
    if admin.id == current_admin_id():
        flash("You cannot deactivate your own account.", "error")
        return redirect(url_for("admin.settings"))
    admin.is_active = not admin.is_active
    db.session.commit()
    record("toggle", "admin", admin.id, {"active": admin.is_active})
    flash("Admin updated.", "success")
    return redirect(url_for("admin.settings"))


@admin_bp.post("/settings/platform")
@role_required("super_admin")
def save_setting():
    form = AppSettingForm()
    if form.validate_on_submit():
        key = form.key.data.strip()
        row = AppSetting.query.filter_by(key=key).first()
        if row is None:
            row = AppSetting(key=key, value=form.value.data, updated_at=utcnow())
            db.session.add(row)
        else:
            row.value = form.value.data
            row.updated_at = utcnow()
        db.session.commit()
        record("update", "setting", row.id, {"key": key})
        flash("Setting saved.", "success")
    return redirect(url_for("admin.settings"))


# ---------------------------------------------------------------- audit


@admin_bp.get("/audit")
@role_required("super_admin")
def audit():
    query = AdminAuditLog.query
    entity_type = request.args.get("entity_type")
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    action = request.args.get("action")
    if action:
        query = query.filter_by(action=action)
    pagination = _page(query.order_by(AdminAuditLog.created_at.desc()), 30)
    entity_types = [
        row[0]
        for row in db.session.query(AdminAuditLog.entity_type)
        .distinct()
        .order_by(AdminAuditLog.entity_type)
    ]
    return render_template(
        "admin/audit.html",
        pagination=pagination,
        entity_type=entity_type,
        action=action,
        entity_types=entity_types,
    )
