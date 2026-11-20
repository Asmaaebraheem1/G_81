"""Jinja admin authentication, pages, guarded actions, and audit tests."""

from __future__ import annotations

from datetime import date

from app.core.db import db
from app.modules.admin.models import Admin, AdminAuditLog, AppSetting
from app.modules.catalog.models import EmissionCategory
from app.modules.records.models import ConsumptionRecord
from app.modules.users.models import User
from tests.conftest import ADMIN_EMAIL, ADMIN_PASSWORD, EDITOR_EMAIL, EDITOR_PASSWORD


def _admin_login(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD):
    return client.post(
        "/admin/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )


def _record(app, data):
    with app.app_context():
        record = ConsumptionRecord(
            user_id=data["user"].id,
            category_id=data["electricity"].id,
            factor_id=data["grid"].id,
            activity_date=date(2026, 6, 15),
            quantity=10,
            unit="kWh",
            factor_grams_co2e_snapshot=233,
            factor_source_snapshot="DEFRA/BEIS (2025), UK",
            emissions_grams=2330,
            status="active",
            source="manual",
        )
        db.session.add(record)
        db.session.commit()
        return record.id


def test_admin_login_and_guards(client, app, data):
    anonymous = client.get("/admin/")
    assert anonymous.status_code == 302
    assert "/admin/login" in anonymous.headers["Location"]

    page = client.get("/admin/login")
    assert page.status_code == 200
    assert b"Sign in" in page.data

    bad = _admin_login(client, password="WrongPass1")
    assert bad.status_code == 401
    assert b"Invalid email or password" in bad.data

    good = _admin_login(client)
    assert good.status_code == 302
    assert good.headers["Location"].endswith("/admin/")
    assert client.get("/admin/").status_code == 200
    assert AdminAuditLog.query.filter_by(action="login").count() == 1

    client.post("/admin/logout")
    assert client.get("/admin/").status_code == 302


def test_all_admin_pages_render(client, app, data):
    record_id = _record(app, data)
    _admin_login(client)
    pages = [
        "/admin/",
        "/admin/users",
        "/admin/users?q=sara&status=active",
        f"/admin/users/{data['user'].id}",
        "/admin/organizations",
        f"/admin/organizations/{data['org_user'].organization_id}",
        "/admin/categories",
        "/admin/factors",
        "/admin/records",
        f"/admin/records/{record_id}",
        "/admin/documents",
        "/admin/plans",
        "/admin/goals",
        "/admin/reports",
        "/admin/challenges",
        "/admin/badges",
        "/admin/notifications",
        "/admin/ai",
        "/admin/content",
        "/admin/settings",
        "/admin/audit",
        "/admin/audit?action=login",
    ]
    for path in pages:
        response = client.get(path)
        assert response.status_code == 200, (path, response.status_code)
    assert b"Dashboard" in client.get("/admin/").data


def test_admin_category_create_edit_toggle(client, app, data):
    _admin_login(client)
    created = client.post(
        "/admin/categories/new",
        data={
            "key": "new-cat",
            "name_en": "New Category",
            "name_ar": "فئة جديدة",
            "description_en": "Demo",
            "description_ar": "تجريبي",
            "icon": "star",
            "color_hex": "#123456",
            "unit_hint": "unit",
            "sort_order": "9",
            "is_active": "y",
        },
        follow_redirects=True,
    )
    assert created.status_code == 200
    row = EmissionCategory.query.filter_by(key="new-cat").first()
    assert row is not None and row.is_active is True

    duplicate = client.post(
        "/admin/categories/new",
        data={"key": "new-cat", "name_en": "Again", "name_ar": "مرة أخرى"},
        follow_redirects=True,
    )
    assert duplicate.status_code == 200
    assert b"already exists" in duplicate.data

    edit = client.post(
        f"/admin/categories/{row.id}/edit",
        data={
            "key": "new-cat",
            "name_en": "Renamed",
            "name_ar": "معاد",
            "is_active": "y",
        },
        follow_redirects=True,
    )
    assert edit.status_code == 200
    assert EmissionCategory.query.get(row.id).name_en == "Renamed"

    toggle = client.post(f"/admin/categories/{row.id}/toggle", follow_redirects=True)
    assert toggle.status_code == 200
    assert EmissionCategory.query.get(row.id).is_active is False
    assert AdminAuditLog.query.filter_by(entity_type="category").count() >= 3
    assert b"Category updated" in toggle.data


def test_admin_factor_create(client, app, data):
    _admin_login(client)
    response = client.post(
        "/admin/factors/new",
        data={
            "category_id": str(data["electricity"].id),
            "key": "test-factor",
            "name_en": "Test factor",
            "name_ar": "عامل تجريبي",
            "activity_type": "test",
            "unit": "kWh",
            "factor_grams_co2e": "100",
            "source_name": "Test source",
            "source_year": "2026",
            "region": "GLOBAL",
            "valid_from": "2026-01-01",
            "is_active": "y",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Factor created" in response.data
    assert b"Test factor" in response.data


def test_admin_settings_and_super_admin_actions(client, app, data):
    _admin_login(client)
    updated = client.post(
        "/admin/settings",
        data={"name": "Renamed Admin", "email": ADMIN_EMAIL, "password": ""},
        follow_redirects=True,
    )
    assert updated.status_code == 200
    assert Admin.query.filter_by(email=ADMIN_EMAIL).first().name == "Renamed Admin"

    created = client.post(
        "/admin/settings/admins",
        data={
            "name": "Second Admin",
            "email": "second-admin@example.com",
            "role": "content_editor",
            "password": "Second123",
        },
        follow_redirects=True,
    )
    assert created.status_code == 200
    second = Admin.query.filter_by(email="second-admin@example.com").first()
    assert second is not None

    toggle = client.post(f"/admin/settings/admins/{second.id}/toggle", follow_redirects=True)
    assert toggle.status_code == 200
    assert Admin.query.get(second.id).is_active is False

    saved = client.post(
        "/admin/settings/platform",
        data={"key": "demo_mode", "value": "true"},
        follow_redirects=True,
    )
    assert saved.status_code == 200
    assert AppSetting.query.filter_by(key="demo_mode").first().value == "true"

    invalid = client.post(
        "/admin/settings/admins",
        data={"name": "", "email": "bad", "role": "content_editor", "password": "x"},
        follow_redirects=True,
    )
    assert invalid.status_code == 200
    assert b"complete every admin field" in invalid.data


def test_content_editor_is_blocked_from_super_admin_pages(client, app, data):
    _admin_login(client, EDITOR_EMAIL, EDITOR_PASSWORD)
    assert client.get("/admin/").status_code == 200
    assert client.get("/admin/settings").status_code == 200
    assert client.get("/admin/audit").status_code == 403
    assert (
        client.post(
            "/admin/settings/admins",
            data={
                "name": "Nope",
                "email": "nope@example.com",
                "role": "content_editor",
                "password": "Nope1234",
            },
        ).status_code
        == 403
    )
    assert (
        client.post("/admin/settings/platform", data={"key": "x", "value": "y"}).status_code == 403
    )


def test_admin_record_status_and_user_action(client, app, data):
    record_id = _record(app, data)
    _admin_login(client)
    response = client.post(
        f"/admin/records/{record_id}/status",
        data={"status": "deleted"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert ConsumptionRecord.query.get(record_id).status == "deleted"

    user = data["user"]
    response = client.post(
        f"/admin/users/{user.id}/action",
        data={"action": "suspend"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert User.query.get(user.id).is_active is False


def test_admin_404_and_error_page(client):
    response = client.get("/admin/does-not-exist")
    assert response.status_code in {302, 404}
    response = client.get("/admin/login")
    assert response.status_code == 200
