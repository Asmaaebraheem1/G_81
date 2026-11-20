"""Catalog, record CRUD/calculation, dashboard, and export tests."""

from __future__ import annotations

from datetime import date

from app.core.db import db
from tests.helpers import auth, record_payload, token_for


def test_catalog_endpoints(client, data):
    categories = client.get("/api/v1/categories")
    assert categories.status_code == 200
    assert len(categories.get_json()["data"]) == 4
    category = client.get(f"/api/v1/categories/{data['electricity'].id}")
    assert category.status_code == 200
    assert category.get_json()["data"]["key"] == "electricity"
    assert client.get("/api/v1/categories/9999").status_code == 404

    factors = client.get(f"/api/v1/factors?category_id={data['electricity'].id}")
    assert factors.status_code == 200
    assert [row["key"] for row in factors.get_json()["data"]] == ["grid_electricity"]
    searched = client.get("/api/v1/factors?q=petrol")
    assert [row["key"] for row in searched.get_json()["data"]] == ["petrol_car"]
    factor = client.get(f"/api/v1/factors/{data['grid'].id}")
    assert factor.status_code == 200
    assert factor.get_json()["data"]["factor_grams_co2e"] == 233
    assert factor.get_json()["data"]["factor_kg_co2e"] == 0.233
    assert client.get("/api/v1/factors/9999").status_code == 404

    alternatives = client.get("/api/v1/alternatives")
    assert alternatives.status_code == 200
    assert len(alternatives.get_json()["data"]) == 2
    filtered = client.get(f"/api/v1/alternatives?category_id={data['transport'].id}")
    assert len(filtered.get_json()["data"]) == 1
    detail = client.get(f"/api/v1/alternatives/{data['alternative'].id}")
    assert detail.status_code == 200
    assert detail.get_json()["data"]["key"] == "led-lighting"

    articles = client.get("/api/v1/content/articles")
    assert articles.status_code == 200
    assert articles.get_json()["data"][0]["slug"] == "how-to-start"
    article = client.get("/api/v1/content/articles/how-to-start")
    assert article.status_code == 200
    assert client.get("/api/v1/content/articles/missing").status_code == 404


def test_inactive_catalog_items_are_hidden(client, data):
    data["electricity"].is_active = False
    data["grid"].is_active = False
    db.session.commit()
    categories = client.get("/api/v1/categories").get_json()["data"]
    assert "electricity" not in [row["key"] for row in categories]
    assert client.get(f"/api/v1/categories/{data['electricity'].id}").status_code == 404
    factors = client.get("/api/v1/factors").get_json()["data"]
    assert "grid_electricity" not in [row["key"] for row in factors]


def test_record_create_list_detail_update_delete(client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    payload = record_payload(data, quantity=100)
    created = client.post("/api/v1/records", headers=headers, json=payload)
    assert created.status_code == 201, created.get_json()
    record = created.get_json()["data"]
    assert record["emissions_grams"] == 23300
    assert record["emissions_kg"] == 23.3
    assert record["factor_grams_co2e_snapshot"] == 233
    assert "DEFRA/BEIS" in record["factor_source_snapshot"]
    assert record["formula"] == ("100 kWh × 233 g CO2e/kWh = 23,300 g CO2e (23.30 kg)")

    listed = client.get("/api/v1/records", headers=headers)
    assert listed.status_code == 200
    assert listed.get_json()["meta"]["total"] == 1
    assert listed.get_json()["data"][0]["id"] == record["id"]

    detail = client.get(f"/api/v1/records/{record['id']}", headers=headers)
    assert detail.status_code == 200
    calculation = client.get(f"/api/v1/records/{record['id']}/calculation", headers=headers)
    assert calculation.status_code == 200
    assert calculation.get_json()["data"]["emissions_grams"] == 23300

    updated = client.patch(
        f"/api/v1/records/{record['id']}",
        headers=headers,
        json={"quantity": 200, "notes": "Updated"},
    )
    assert updated.status_code == 200
    assert updated.get_json()["data"]["emissions_grams"] == 46600

    deleted = client.delete(f"/api/v1/records/{record['id']}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.get_json()["data"]["deleted"] is True
    assert client.get(f"/api/v1/records/{record['id']}", headers=headers).status_code == 404


def test_record_validation_and_ownership(client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    future = client.post(
        "/api/v1/records",
        headers=headers,
        json=record_payload(data, activity_date=date(2027, 1, 1)),
    )
    assert future.status_code == 422

    wrong_unit = client.post(
        "/api/v1/records",
        headers=headers,
        json=record_payload(data, unit="litres"),
    )
    assert wrong_unit.status_code == 422

    wrong_factor = client.post(
        "/api/v1/records",
        headers=headers,
        json={
            **record_payload(data),
            "category_id": data["transport"].id,
            "factor_id": data["grid"].id,
        },
    )
    assert wrong_factor.status_code == 422

    missing_category = client.post(
        "/api/v1/records",
        headers=headers,
        json={**record_payload(data), "category_id": 9999},
    )
    assert missing_category.status_code == 422

    created = client.post("/api/v1/records", headers=headers, json=record_payload(data)).get_json()[
        "data"
    ]
    other_token = token_for(client, "ahmad@example.com", "User123!")
    other_headers = auth(other_token)
    assert client.get(f"/api/v1/records/{created['id']}", headers=other_headers).status_code == 404
    assert (
        client.delete(f"/api/v1/records/{created['id']}", headers=other_headers).status_code == 404
    )


def test_record_query_filters_and_pagination(client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    for index, quantity in enumerate([10, 20, 30]):
        response = client.post(
            "/api/v1/records",
            headers=headers,
            json=record_payload(
                data,
                quantity=quantity,
                activity_date=date(2026, 6, 10 + index),
            ),
        )
        assert response.status_code == 201

    filtered = client.get(
        "/api/v1/records?from=2026-06-11&to=2026-06-12&sort=emissions_grams",
        headers=headers,
    )
    assert filtered.status_code == 200
    assert filtered.get_json()["meta"]["total"] == 2
    assert filtered.get_json()["data"][0]["emissions_grams"] == 20 * 233

    searched = client.get("/api/v1/records?q=activity", headers=headers)
    assert searched.get_json()["meta"]["total"] == 3

    page = client.get("/api/v1/records?page=2&per_page=2", headers=headers)
    assert page.status_code == 200
    assert page.get_json()["meta"]["pages"] == 2
    assert len(page.get_json()["data"]) == 1

    invalid = client.get("/api/v1/records?from=2026-06-01", headers=headers)
    assert invalid.status_code == 422
    invalid = client.get("/api/v1/records?from=2026-06-10&to=2026-06-01", headers=headers)
    assert invalid.status_code == 422
    invalid = client.get("/api/v1/records?per_page=200", headers=headers)
    assert invalid.status_code == 422


def test_dashboard_reports_and_csv(client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    for quantity, factor in [
        (100, data["grid"]),
        (50, data["car"]),
        (2, data["beef"]),
    ]:
        client.post(
            "/api/v1/records",
            headers=headers,
            json=record_payload(data, quantity=quantity, factor=factor),
        )

    dashboard = client.get("/api/v1/dashboard/summary", headers=headers)
    assert dashboard.status_code == 200
    body = dashboard.get_json()["data"]
    assert body["totals"]["records"] == 3
    assert body["totals"]["emissions_grams"] == 23300 + 8500 + 120000
    assert body["categories"][0]["key"] == "food"
    assert len(body["recent_records"]) == 3

    summary = client.get("/api/v1/reports/summary?period=year", headers=headers)
    assert summary.status_code == 200
    assert summary.get_json()["data"]["period"]["from"] == "2026-01-01"

    trend = client.get("/api/v1/reports/trend?months=3", headers=headers)
    assert trend.status_code == 200
    assert len(trend.get_json()["data"]["points"]) == 3

    categories = client.get("/api/v1/reports/categories", headers=headers)
    assert categories.status_code == 200
    assert categories.get_json()["data"]["total_grams"] == 151800

    top = client.get("/api/v1/reports/top-activities?limit=2", headers=headers)
    assert top.status_code == 200
    assert len(top.get_json()["data"]["activities"]) == 2
    assert top.get_json()["data"]["activities"][0]["name_en"] == "Beef"

    comparison = client.get("/api/v1/reports/comparison", headers=headers)
    assert comparison.status_code == 200
    assert "change_percent" in comparison.get_json()["data"]

    export = client.get(
        "/api/v1/reports/export.csv?from=2026-06-01&to=2026-06-30",
        headers=headers,
    )
    assert export.status_code == 200
    assert export.mimetype.startswith("text/csv")
    assert "emissions_grams" in export.get_data(as_text=True)
    assert "Beef" in export.get_data(as_text=True)
    assert "attachment" in export.headers["Content-Disposition"]

    invalid = client.get(
        "/api/v1/reports/export.csv?from=2026-06-30&to=2026-06-01",
        headers=headers,
    )
    assert invalid.status_code == 422
    assert client.get("/api/v1/dashboard/summary").status_code == 401


def test_reports_with_no_records(client, data):
    token = token_for(client, "ahmad@example.com", "User123!")
    headers = auth(token)
    dashboard = client.get("/api/v1/dashboard/summary", headers=headers)
    assert dashboard.status_code == 200
    assert dashboard.get_json()["data"]["totals"]["emissions_grams"] == 0
    assert dashboard.get_json()["data"]["top_category"] is None
    trend = client.get("/api/v1/reports/trend", headers=headers)
    assert trend.get_json()["data"]["total_grams"] == 0
    comparison = client.get("/api/v1/reports/comparison", headers=headers)
    assert comparison.get_json()["data"]["change_percent"] == 0
