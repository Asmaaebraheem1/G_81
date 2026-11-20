"""AI fallbacks and private document workflow tests."""

from __future__ import annotations

import io

from PIL import Image

from tests.helpers import auth, record_payload, token_for


def _png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (12, 12), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def _upload(client, headers, consent=True, filename="bill.png", content=None):
    return client.post(
        "/api/v1/documents",
        headers=headers,
        data={
            "file": (io.BytesIO(content if content is not None else _png_bytes()), filename),
            "consent": "true" if consent else "false",
        },
        content_type="multipart/form-data",
    )


def test_ai_status_and_rule_fallbacks(client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    status = client.get("/api/v1/ai/status", headers=headers)
    assert status.status_code == 200
    body = status.get_json()["data"]
    assert body["model"] == "openrouter/free"
    assert body["enabled"] is False
    assert body["configured"] is False

    client.post("/api/v1/records", headers=headers, json=record_payload(data, quantity=100))
    chat = client.post(
        "/api/v1/ai/chat",
        headers=headers,
        json={"message": "What should I do first?", "locale": "en"},
    )
    assert chat.status_code == 503
    error = chat.get_json()["error"]
    assert error["code"] == "ai_disabled"
    assert error["details"]["fallback"]["total_kg"] == 23.3
    assert "disclaimer" in error["details"]

    insights = client.post(
        "/api/v1/ai/insights",
        headers=headers,
        json={"period": "month", "locale": "en"},
    )
    assert insights.status_code == 200
    body = insights.get_json()["data"]
    assert body["source"] == "rules"
    assert "calculated" in body["narrative"].lower()
    assert body["top_sources"][0]["name_en"] == "Electricity"
    assert body["opportunities"]
    assert body["calculated_context"]["total_kg"] == 23.3

    summary = client.post(
        "/api/v1/ai/summary",
        headers=headers,
        json={"period": "month", "locale": "ar"},
    )
    assert summary.status_code == 200
    assert summary.get_json()["data"]["source"] == "rules"
    assert summary.get_json()["data"]["narrative"].startswith("بلغ")


def test_ai_screenshot_mode_chat_conversation_and_flags(app, client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    client.post("/api/v1/records", headers=headers, json=record_payload(data, quantity=20))
    app.config["AI_SCREENSHOT_MODE"] = True

    chat = client.post(
        "/api/v1/ai/chat",
        headers=headers,
        json={"message": "Explain my footprint", "locale": "en"},
    )
    assert chat.status_code == 200, chat.get_json()
    body = chat.get_json()["data"]
    assert body["model"] == "openrouter/free (screenshot mode)"
    assert body["conversation_id"]
    assert body["message_id"]
    assert body["context"]["total_kg"] == 4.66

    listing = client.get("/api/v1/ai/conversations", headers=headers)
    assert listing.status_code == 200
    assert len(listing.get_json()["data"]) == 1

    detail = client.get(f"/api/v1/ai/conversations/{body['conversation_id']}", headers=headers)
    assert detail.status_code == 200
    assert len(detail.get_json()["data"]["messages"]) == 2

    flag = client.post(
        "/api/v1/ai/flag",
        headers=headers,
        json={
            "message_id": body["message_id"],
            "reason": "inaccurate",
            "notes": "Please review this.",
        },
    )
    assert flag.status_code == 201
    assert flag.get_json()["data"]["status"] == "open"

    continued = client.post(
        "/api/v1/ai/chat",
        headers=headers,
        json={
            "message": "And next?",
            "conversation_id": body["conversation_id"],
            "locale": "en",
        },
    )
    assert continued.status_code == 200
    detail = client.get(f"/api/v1/ai/conversations/{body['conversation_id']}", headers=headers)
    assert len(detail.get_json()["data"]["messages"]) == 4

    deleted = client.delete(f"/api/v1/ai/conversations/{body['conversation_id']}", headers=headers)
    assert deleted.status_code == 200
    assert (
        client.get(
            f"/api/v1/ai/conversations/{body['conversation_id']}", headers=headers
        ).status_code
        == 404
    )
    app.config["AI_SCREENSHOT_MODE"] = False


def test_ai_conversation_isolation_and_flag_errors(app, client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    other_token = token_for(client, "ahmad@example.com", "User123!")
    other_headers = auth(other_token)
    app.config["AI_SCREENSHOT_MODE"] = True
    created = client.post(
        "/api/v1/ai/chat",
        headers=headers,
        json={"message": "Hello", "locale": "en"},
    ).get_json()["data"]
    assert (
        client.get(
            f"/api/v1/ai/conversations/{created['conversation_id']}",
            headers=other_headers,
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/api/v1/ai/conversations/{created['conversation_id']}",
            headers=other_headers,
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/ai/flag",
            headers=other_headers,
            json={"message_id": created["message_id"], "reason": "unsafe"},
        ).status_code
        == 404
    )
    app.config["AI_SCREENSHOT_MODE"] = False


def test_document_upload_list_download_delete(client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    uploaded = _upload(client, headers)
    assert uploaded.status_code == 201, uploaded.get_json()
    document = uploaded.get_json()["data"]
    assert document["mime_type"] == "image/png"
    assert document["status"] == "uploaded"
    assert document["ai_consent"] is True
    assert document["download_url"].endswith(f"/{document['id']}/download")

    listing = client.get("/api/v1/documents", headers=headers)
    assert listing.status_code == 200
    assert len(listing.get_json()["data"]) == 1
    assert client.get("/api/v1/documents?status=uploaded", headers=headers).status_code == 200
    detail = client.get(f"/api/v1/documents/{document['id']}", headers=headers)
    assert detail.status_code == 200

    download = client.get(f"/api/v1/documents/{document['id']}/download", headers=headers)
    assert download.status_code == 200
    assert download.data.startswith(b"\x89PNG")
    assert "attachment" in download.headers["Content-Disposition"]

    other_token = token_for(client, "ahmad@example.com", "User123!")
    other_headers = auth(other_token)
    assert (
        client.get(f"/api/v1/documents/{document['id']}", headers=other_headers).status_code == 404
    )

    deleted = client.delete(f"/api/v1/documents/{document['id']}", headers=headers)
    assert deleted.status_code == 200
    assert client.get("/api/v1/documents", headers=headers).get_json()["data"] == []


def test_document_upload_validation(client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    assert client.post("/api/v1/documents", headers=headers).status_code == 422
    assert _upload(client, headers, filename="bad.txt").status_code == 422
    assert _upload(client, headers, content=b"").status_code == 422
    assert _upload(client, headers, content=b"not an image").status_code == 422
    assert _upload(client, headers, filename="fake.png", content=b"%PDF-1.4").status_code == 201


def test_document_extraction_consent_and_ai_disabled(client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    no_consent = _upload(client, headers, consent=False).get_json()["data"]
    response = client.post(f"/api/v1/documents/{no_consent['id']}/extract", headers=headers)
    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "consent_required"

    document = _upload(client, headers, consent=True).get_json()["data"]
    response = client.post(f"/api/v1/documents/{document['id']}/extract", headers=headers)
    assert response.status_code == 503
    assert response.get_json()["error"]["code"] == "ai_disabled"
    assert response.get_json()["error"]["details"]["fallback"] == "manual_entry"


def test_document_screenshot_extraction_and_manual_confirm(app, client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    document = _upload(client, headers, consent=True).get_json()["data"]
    app.config["AI_SCREENSHOT_MODE"] = True
    extracted = client.post(f"/api/v1/documents/{document['id']}/extract", headers=headers)
    assert extracted.status_code == 200
    body = extracted.get_json()["data"]
    assert body["status"] == "extracted"
    assert body["fields"]["consumption_value"] == 120.5

    confirmed = client.post(
        f"/api/v1/documents/{document['id']}/confirm",
        headers=headers,
        json={
            **record_payload(data, quantity=120.5),
            "vendor": "City Electric",
        },
    )
    assert confirmed.status_code == 201, confirmed.get_json()
    body = confirmed.get_json()["data"]
    assert body["record"]["emissions_grams"] == 28077
    assert body["document"]["status"] == "confirmed"
    assert body["document"]["record_id"] == body["record"]["id"]

    duplicate = client.post(
        f"/api/v1/documents/{document['id']}/confirm",
        headers=headers,
        json=record_payload(data, quantity=1),
    )
    assert duplicate.status_code == 409
    assert client.delete(f"/api/v1/documents/{document['id']}", headers=headers).status_code == 409
    app.config["AI_SCREENSHOT_MODE"] = False


def test_document_confirmation_requires_valid_factor(client, data):
    token = token_for(client, "sara@example.com", "User123!")
    headers = auth(token)
    document = _upload(client, headers, consent=True).get_json()["data"]
    response = client.post(
        f"/api/v1/documents/{document['id']}/confirm",
        headers=headers,
        json={
            **record_payload(data),
            "category_id": data["transport"].id,
            "factor_id": data["grid"].id,
        },
    )
    assert response.status_code == 422
