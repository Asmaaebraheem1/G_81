"""Goal baselines/progress and reduction-plan generation tests."""

from __future__ import annotations

from datetime import date

from app.modules.goals.models import Goal
from tests.helpers import auth, record_payload, token_for


def _add_baseline(client, headers, data, quantity=100):
    response = client.post(
        "/api/v1/records",
        headers=headers,
        json=record_payload(data, quantity=quantity, activity_date=date(2026, 3, 15)),
    )
    assert response.status_code == 201
    return response.get_json()["data"]


def test_goal_create_progress_update_cancel(client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    baseline = _add_baseline(client, headers, data, 100)
    goal_payload = {
        "title": "Reduce summer electricity",
        "target_percent": 20,
        "period_type": "monthly",
        "start_date": "2026-04-01",
        "end_date": "2026-07-31",
        "baseline_start": "2026-03-01",
        "baseline_end": "2026-03-31",
    }
    created = client.post("/api/v1/goals", headers=headers, json=goal_payload)
    assert created.status_code == 201, created.get_json()
    goal = created.get_json()["data"]
    assert goal["baseline_emissions_grams"] == baseline["emissions_grams"]
    assert goal["target_emissions_grams"] == round(baseline["emissions_grams"] * 0.8)
    assert goal["status"] == "active"
    assert goal["achieved_percent"] >= 0

    listed = client.get("/api/v1/goals", headers=headers)
    assert listed.status_code == 200
    assert len(listed.get_json()["data"]) == 1
    assert client.get("/api/v1/goals?status=active", headers=headers).status_code == 200
    assert client.get("/api/v1/goals?status=missed", headers=headers).get_json()["data"] == []

    detail = client.get(f"/api/v1/goals/{goal['id']}", headers=headers)
    assert detail.status_code == 200
    assert client.get(f"/api/v1/goals/{goal['id']}/progress", headers=headers).status_code == 200

    updated = client.patch(
        f"/api/v1/goals/{goal['id']}",
        headers=headers,
        json={"title": "Updated title"},
    )
    assert updated.status_code == 200
    assert updated.get_json()["data"]["title"] == "Updated title"

    bad_update = client.patch(
        f"/api/v1/goals/{goal['id']}",
        headers=headers,
        json={"start_date": "2026-07-01", "end_date": "2026-06-01"},
    )
    assert bad_update.status_code == 422

    cancelled = client.delete(f"/api/v1/goals/{goal['id']}", headers=headers)
    assert cancelled.status_code == 200
    assert cancelled.get_json()["data"]["cancelled"] is True
    assert Goal.query.get(goal["id"]).status == "cancelled"


def test_goal_without_baseline_and_invalid_dates(client, data):
    token = token_for(client, "ahmad@example.com", "User123!")
    headers = auth(token)
    payload = {
        "title": "No baseline",
        "target_percent": 10,
        "period_type": "monthly",
        "start_date": "2026-04-01",
        "end_date": "2026-06-30",
    }
    response = client.post("/api/v1/goals", headers=headers, json=payload)
    assert response.status_code == 422
    assert "baseline" in response.get_json()["error"]["message"].lower()

    response = client.post(
        "/api/v1/goals",
        headers=headers,
        json={**payload, "start_date": "2026-07-01", "end_date": "2026-06-01"},
    )
    assert response.status_code == 422


def test_goal_uses_default_baseline_window(client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    _add_baseline(client, headers, data, 50)
    response = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Default baseline",
            "target_percent": 25,
            "period_type": "monthly",
            "start_date": "2026-04-01",
            "end_date": "2026-06-30",
        },
    )
    assert response.status_code == 201
    assert response.get_json()["data"]["baseline_start"] == "2025-12-31"
    assert response.get_json()["data"]["baseline_end"] == "2026-03-31"


def test_plan_generation_template_and_action_tracking(client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    for quantity, factor in [(100, data["grid"]), (20, data["car"])]:
        assert (
            client.post(
                "/api/v1/records",
                headers=headers,
                json=record_payload(data, quantity=quantity, factor=factor),
            ).status_code
            == 201
        )

    generated = client.post(
        "/api/v1/plans/generate",
        headers=headers,
        json={"period": "month", "locale": "en"},
    )
    assert generated.status_code == 201, generated.get_json()
    plan = generated.get_json()["data"]
    assert plan["source"] == "template"
    assert plan["status"] == "draft"
    assert len(plan["actions"]) == 2
    for action in plan["actions"]:
        assert action["estimated_saving_grams"] is not None
        assert action["saving_assumption"]
        assert "not an ai estimate" in action["saving_assumption"].lower()

    listed = client.get("/api/v1/plans", headers=headers)
    assert listed.status_code == 200
    assert len(listed.get_json()["data"]) == 1
    assert client.get("/api/v1/plans?status=draft", headers=headers).status_code == 200

    detail = client.get(f"/api/v1/plans/{plan['id']}", headers=headers)
    assert detail.status_code == 200
    assert len(detail.get_json()["data"]["actions"]) == 2

    updated = client.patch(
        f"/api/v1/plans/{plan['id']}",
        headers=headers,
        json={"title": "My plan", "status": "active"},
    )
    assert updated.status_code == 200
    assert updated.get_json()["data"]["title"] == "My plan"

    action_id = plan["actions"][0]["id"]
    action = client.patch(
        f"/api/v1/plans/{plan['id']}/actions/{action_id}",
        headers=headers,
        json={"status": "completed"},
    )
    assert action.status_code == 200
    assert action.get_json()["data"]["status"] == "completed"

    progress = client.get(f"/api/v1/plans/{plan['id']}/progress", headers=headers)
    assert progress.status_code == 200
    body = progress.get_json()["data"]
    assert body["actions_completed"] == 1
    assert body["progress_percent"] == 50.0
    assert body["estimated_saving_grams"] > 0

    missing = client.get("/api/v1/plans/9999", headers=headers)
    assert missing.status_code == 404


def test_plan_requires_records_and_arabic_template(client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    response = client.post(
        "/api/v1/plans/generate",
        headers=headers,
        json={"period": "month", "locale": "ar"},
    )
    assert response.status_code == 422

    client.post("/api/v1/records", headers=headers, json=record_payload(data, quantity=10))
    response = client.post(
        "/api/v1/plans/generate",
        headers=headers,
        json={"period": "month", "locale": "ar"},
    )
    assert response.status_code == 201
    plan = response.get_json()["data"]
    assert plan["locale"] == "ar"
    assert "خطة" in plan["title"]
    assert "الخادم" in plan["summary"]


def test_plan_generation_with_goal(client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    _add_baseline(client, headers, data, 100)
    client.post(
        "/api/v1/records",
        headers=headers,
        json=record_payload(data, quantity=50, activity_date=date(2026, 6, 1)),
    )
    goal = client.post(
        "/api/v1/goals",
        headers=headers,
        json={
            "title": "Goal",
            "target_percent": 20,
            "period_type": "monthly",
            "start_date": "2026-04-01",
            "end_date": "2026-06-30",
        },
    ).get_json()["data"]
    response = client.post(
        "/api/v1/plans/generate",
        headers=headers,
        json={"period": "month", "goal_id": goal["id"], "locale": "en"},
    )
    assert response.status_code == 201
    assert response.get_json()["data"]["goal_id"] == goal["id"]
