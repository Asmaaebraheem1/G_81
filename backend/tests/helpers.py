"""Small test helpers shared by API tests."""

from __future__ import annotations

from datetime import date


def login(client, email: str, password: str):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def token_for(client, email: str, password: str) -> str:
    response = login(client, email, password)
    assert response.status_code == 200, response.get_json()
    return response.get_json()["data"]["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def record_payload(data, quantity=100, activity_date=None, factor=None, unit=None):
    factor = factor or data["grid"]
    return {
        "category_id": factor.category_id,
        "factor_id": factor.id,
        "activity_date": (activity_date or date(2026, 6, 15)).isoformat(),
        "quantity": quantity,
        "unit": unit or factor.unit,
        "notes": "Test activity",
    }
