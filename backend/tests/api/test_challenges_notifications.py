"""Challenges, achievements, notifications, and recommendation tests."""

from __future__ import annotations

from datetime import date, datetime

from app.core.db import db
from app.modules.challenges.models import ChallengeParticipant, PointsLedger, UserBadge
from app.modules.notifications.models import Notification, NotificationPreference
from app.modules.users.models import UserProfile
from tests.helpers import auth, record_payload, token_for


def test_challenge_join_progress_award_and_achievements(client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    challenge = data["challenge"]

    listing = client.get("/api/v1/challenges", headers=headers)
    assert listing.status_code == 200
    assert listing.get_json()["data"][0]["challenge_status"] == "active"
    assert client.get("/api/v1/challenges?status=upcoming", headers=headers).status_code == 200

    detail = client.get(f"/api/v1/challenges/{challenge.id}", headers=headers)
    assert detail.status_code == 200
    assert detail.get_json()["data"]["participation"] is None

    joined = client.post(f"/api/v1/challenges/{challenge.id}/join", headers=headers)
    assert joined.status_code == 201
    assert joined.get_json()["data"]["status"] == "joined"

    # A second join is idempotent but the endpoint keeps its 201 contract.
    again = client.post(f"/api/v1/challenges/{challenge.id}/join", headers=headers)
    assert again.status_code == 201
    assert again.get_json()["data"]["id"] == joined.get_json()["data"]["id"]

    for day in (10, 11):
        assert (
            client.post(
                "/api/v1/records",
                headers=headers,
                json=record_payload(data, quantity=10, activity_date=date(2026, 6, day)),
            ).status_code
            == 201
        )

    progress = client.get(f"/api/v1/challenges/{challenge.id}/progress", headers=headers)
    assert progress.status_code == 200
    body = progress.get_json()["data"]
    assert body["value"] == 2
    assert body["percent"] == 100
    assert body["status"] == "completed"
    assert body["verified"] is True

    participant = ChallengeParticipant.query.filter_by(
        user_id=data["user"].id, challenge_id=challenge.id
    ).first()
    assert participant.status == "completed"
    assert PointsLedger.query.filter_by(user_id=data["user"].id).count() == 1
    assert UserBadge.query.filter_by(user_id=data["user"].id).count() == 1
    assert Notification.query.filter_by(user_id=data["user"].id, type="challenge").count() == 1

    achievements = client.get("/api/v1/achievements", headers=headers)
    assert achievements.status_code == 200
    achievement_body = achievements.get_json()["data"]
    assert achievement_body["points"] == 20
    assert len(achievement_body["badges"]) == 1
    assert achievement_body["milestones"]["records"] == 2


def test_challenge_manual_progress_and_errors(client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    challenge = data["challenge"]
    missing = client.post(
        f"/api/v1/challenges/{challenge.id}/progress",
        headers=headers,
        json={"value": 1},
    )
    assert missing.status_code == 409

    client.post(f"/api/v1/challenges/{challenge.id}/join", headers=headers)
    one = client.post(
        f"/api/v1/challenges/{challenge.id}/progress",
        headers=headers,
        json={"value": 1},
    )
    assert one.status_code == 200
    assert one.get_json()["data"]["status"] == "in_progress"
    two = client.post(
        f"/api/v1/challenges/{challenge.id}/progress",
        headers=headers,
        json={"value": 2},
    )
    assert two.status_code == 200
    assert two.get_json()["data"]["status"] == "completed"
    assert client.get("/api/v1/challenges/9999", headers=headers).status_code == 404


def test_leaderboard_opt_in_and_privacy(client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    before = client.get("/api/v1/leaderboard", headers=headers)
    assert before.status_code == 200
    assert before.get_json()["data"]["opt_in"] is False
    assert before.get_json()["data"]["entries"] == []

    profile = UserProfile.query.filter_by(user_id=data["user"].id).first()
    profile.leaderboard_opt_in = True
    profile.leaderboard_alias = "Green Sara"
    db.session.add(
        PointsLedger(
            user_id=data["user"].id,
            points=50,
            reason="Test",
            reference_type="test",
            created_at=datetime(2026, 6, 15, 12, 0),
        )
    )
    db.session.commit()

    after = client.get("/api/v1/leaderboard?period=year", headers=headers)
    assert after.status_code == 200
    body = after.get_json()["data"]
    assert body["opt_in"] is True
    assert body["entries"][0]["alias"] == "Green Sara"
    assert body["entries"][0]["points"] == 50
    assert body["entries"][0]["is_me"] is True
    assert "email" not in str(body["entries"]).lower()


def test_notifications_and_preferences(client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    listing = client.get("/api/v1/notifications", headers=headers)
    assert listing.status_code == 200
    body = listing.get_json()["data"]
    assert body["unread_count"] == 1
    assert body["notifications"][0]["title_en"] == "Welcome"

    notification_id = body["notifications"][0]["id"]
    read = client.patch(f"/api/v1/notifications/{notification_id}/read", headers=headers)
    assert read.status_code == 200
    assert read.get_json()["data"]["is_read"] is True
    assert (
        client.get("/api/v1/notifications", headers=headers).get_json()["data"]["unread_count"] == 0
    )
    assert client.patch("/api/v1/notifications/9999/read", headers=headers).status_code == 404

    preferences = client.get("/api/v1/notification-preferences", headers=headers)
    assert preferences.status_code == 200
    assert len(preferences.get_json()["data"]) == 7
    assert all(item["enabled"] for item in preferences.get_json()["data"])

    updated = client.patch(
        "/api/v1/notification-preferences",
        headers=headers,
        json={"preferences": [{"type": "reminder", "enabled": False}]},
    )
    assert updated.status_code == 200
    reminder = [x for x in updated.get_json()["data"] if x["type"] == "reminder"][0]
    assert reminder["enabled"] is False
    assert NotificationPreference.query.filter_by(user_id=data["user"].id).count() == 1

    all_read = client.post("/api/v1/notifications/read-all", headers=headers)
    assert all_read.status_code == 200


def test_significant_increase_notification(client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    # Previous month is lower, current month is much higher.
    client.post(
        "/api/v1/records",
        headers=headers,
        json=record_payload(data, quantity=10, activity_date=date(2026, 5, 15)),
    )
    client.post(
        "/api/v1/records",
        headers=headers,
        json=record_payload(data, quantity=100, activity_date=date(2026, 6, 15)),
    )
    alerts = Notification.query.filter_by(user_id=data["user"].id, type="alert").all()
    assert len(alerts) == 1
    assert "increased" in alerts[0].title_en.lower()


def test_alternatives_recommended_saved_and_isolated(client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    client.post("/api/v1/records", headers=headers, json=record_payload(data, quantity=10))
    recommended = client.get("/api/v1/alternatives/recommended?locale=en", headers=headers)
    assert recommended.status_code == 200
    body = recommended.get_json()["data"]
    assert body["source"] == "rules"
    assert body["alternatives"][0]["key"] == "led-lighting"
    assert body["alternatives"][0]["recommended"] is True
    assert "not AI-generated" in body["note"]

    alternative = data["alternative"]
    saved = client.post(
        f"/api/v1/alternatives/{alternative.id}/save",
        headers=headers,
        json={"status": "accepted"},
    )
    assert saved.status_code == 201
    assert saved.get_json()["data"]["status"] == "accepted"
    listing = client.get("/api/v1/alternatives/saved", headers=headers)
    assert len(listing.get_json()["data"]) == 1
    assert (
        client.post(
            f"/api/v1/alternatives/{alternative.id}/save",
            headers=headers,
            json={"status": "saved"},
        ).status_code
        == 201
    )
    assert (
        client.get("/api/v1/alternatives/saved", headers=headers).get_json()["data"][0]["status"]
        == "saved"
    )

    other_token = token_for(client, "ahmad@example.com", "User123!")
    assert (
        client.get("/api/v1/alternatives/saved", headers=auth(other_token)).get_json()["data"] == []
    )
    assert (
        client.post(
            "/api/v1/alternatives/9999/save",
            headers=headers,
            json={"status": "saved"},
        ).status_code
        == 404
    )
