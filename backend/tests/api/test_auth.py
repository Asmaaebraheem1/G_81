"""Authentication, profile, organization, token rotation, and logout tests."""

from __future__ import annotations

from app.core.db import db
from app.modules.users.models import RefreshToken, User
from tests.helpers import auth, login, token_for


def test_health_is_public(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.get_json()["data"]
    assert body["status"] == "ok"
    assert body["ai_model"] == "openrouter/free"
    assert client.get("/health").status_code == 200


def test_register_login_me_and_profile(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "password": "Newpass123",
            "full_name": "New User",
            "account_type": "individual",
            "locale": "en",
            "household_size": 2,
        },
    )
    assert response.status_code == 201
    body = response.get_json()["data"]
    assert body["user"]["email"] == "new@example.com"
    assert body["access_token"] and body["refresh_token"]
    assert body["token_type"] == "Bearer"

    duplicate = client.post(
        "/api/v1/auth/register",
        json={
            "email": "NEW@example.com",
            "password": "Newpass123",
            "full_name": "Duplicate",
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.get_json()["error"]["code"] == "conflict"

    assert client.get("/api/v1/auth/me").status_code == 401
    headers = auth(body["access_token"])
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.get_json()["data"]["profile"]["household_size"] == 2

    updated = client.patch(
        "/api/v1/auth/me",
        headers=headers,
        json={"full_name": "Updated Name", "locale": "ar", "timezone": "Africa/Cairo"},
    )
    assert updated.status_code == 200
    assert updated.get_json()["data"]["full_name"] == "Updated Name"
    assert updated.get_json()["data"]["locale"] == "ar"

    profile = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={
            "phone": "+201000000000",
            "city": "Cairo",
            "leaderboard_opt_in": True,
            "onboarding_completed": True,
        },
    )
    assert profile.status_code == 422  # alias is required when opting in
    profile = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={
            "city": "Cairo",
            "leaderboard_opt_in": True,
            "leaderboard_alias": "Green Sara",
            "onboarding_completed": True,
        },
    )
    assert profile.status_code == 200
    assert profile.get_json()["data"]["leaderboard_alias"] == "Green Sara"
    assert client.get("/api/v1/profile", headers=headers).status_code == 200


def test_register_validation_and_organization_flow(client):
    bad = client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "Newpass123", "full_name": "X"},
    )
    assert bad.status_code == 422
    assert bad.get_json()["error"]["code"] == "validation_error"

    missing_org = client.post(
        "/api/v1/auth/register",
        json={
            "email": "org2@example.com",
            "password": "Newpass123",
            "full_name": "Org Two",
            "account_type": "organization",
        },
    )
    assert missing_org.status_code == 422

    created = client.post(
        "/api/v1/auth/register",
        json={
            "email": "org2@example.com",
            "password": "Newpass123",
            "full_name": "Org Two",
            "account_type": "organization",
            "organization_name": "Second Org",
        },
    )
    assert created.status_code == 201
    body = created.get_json()["data"]
    assert body["user"]["organization_id"] is not None
    headers = auth(body["access_token"])

    org = client.get("/api/v1/organization", headers=headers)
    assert org.status_code == 200
    assert org.get_json()["data"]["name_en"] == "Second Org"

    updated = client.patch(
        "/api/v1/organization",
        headers=headers,
        json={"industry": "Services", "city": "Riyadh", "size": "1-10"},
    )
    assert updated.status_code == 200
    assert updated.get_json()["data"]["industry"] == "Services"


def test_non_organization_cannot_read_or_edit_organization(client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    response = client.get("/api/v1/organization", headers=headers)
    assert response.status_code == 403
    response = client.patch(
        "/api/v1/organization",
        headers=headers,
        json={"industry": "Nope"},
    )
    assert response.status_code == 403


def test_login_errors_and_inactive_account(app, client):
    response = login(client, "sara@example.com", "WrongPass1")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "invalid_credentials"

    user = User.query.filter_by(email="sara@example.com").first()
    user.is_active = False
    db.session.commit()
    response = login(client, "sara@example.com", "User123!")
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "account_inactive"


def test_refresh_rotation_and_reuse(app, client):
    first = login(client, "sara@example.com", "User123!").get_json()["data"]
    refresh = first["refresh_token"]
    response = client.post(
        "/api/v1/auth/refresh",
        headers=auth(refresh),
    )
    assert response.status_code == 200
    rotated = response.get_json()["data"]
    assert rotated["refresh_token"] != refresh

    reused = client.post("/api/v1/auth/refresh", headers=auth(refresh))
    assert reused.status_code == 401
    assert reused.get_json()["error"]["code"] == "token_revoked"

    # An access token cannot be used as a refresh token.
    invalid = client.post("/api/v1/auth/refresh", headers=auth(first["access_token"]))
    assert invalid.status_code in {401, 422}


def test_change_password_revokes_tokens(app, client):
    first = login(client, "sara@example.com", "User123!").get_json()["data"]
    headers = auth(first["access_token"])
    wrong = client.patch(
        "/api/v1/auth/password",
        headers=headers,
        json={"current_password": "Wrong123", "new_password": "Newpass123"},
    )
    assert wrong.status_code == 401

    changed = client.patch(
        "/api/v1/auth/password",
        headers=headers,
        json={"current_password": "User123!", "new_password": "Newpass123"},
    )
    assert changed.status_code == 200
    assert login(client, "sara@example.com", "User123!").status_code == 401
    assert login(client, "sara@example.com", "Newpass123").status_code == 200
    # The pre-change token is revoked; the successful login above created one new token.
    assert RefreshToken.query.filter_by(revoked_at=None).count() == 1
    assert RefreshToken.query.count() == 2


def test_logout_single_and_all_devices(app, client):
    first = login(client, "sara@example.com", "User123!").get_json()["data"]
    second = login(client, "sara@example.com", "User123!").get_json()["data"]
    headers = auth(first["access_token"])
    response = client.post(
        "/api/v1/auth/logout",
        headers=headers,
        json={"refresh_token": first["refresh_token"]},
    )
    assert response.status_code == 200
    assert (
        client.post("/api/v1/auth/refresh", headers=auth(first["refresh_token"])).status_code == 401
    )
    assert (
        client.post("/api/v1/auth/refresh", headers=auth(second["refresh_token"])).status_code
        == 200
    )

    third = login(client, "sara@example.com", "User123!").get_json()["data"]
    response = client.post(
        "/api/v1/auth/logout",
        headers=auth(third["access_token"]),
        json={"all_devices": True},
    )
    assert response.status_code == 200
    assert RefreshToken.query.filter_by(revoked_at=None).count() == 0


def test_logout_rejects_invalid_refresh_token_and_type(app, client):
    session = login(client, "sara@example.com", "User123!").get_json()["data"]
    headers = auth(session["access_token"])
    response = client.post(
        "/api/v1/auth/logout",
        headers=headers,
        json={"refresh_token": "not-a-token"},
    )
    assert response.status_code == 401
    response = client.post(
        "/api/v1/auth/logout",
        headers=headers,
        json={"refresh_token": 123},
    )
    assert response.status_code == 422
