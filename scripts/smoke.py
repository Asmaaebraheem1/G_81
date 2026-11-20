#!/usr/bin/env python3
"""Small end-to-end smoke test for a running CarbonWise backend.

It uses only the standard library so it can run on a clean Windows demo machine.
Start the backend first (``scripts\\demo.cmd`` or the Flask command), then run:

    backend\\.venv\\Scripts\\python.exe scripts\\smoke.py

Exit code 0 means every check passed.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_BASE = "http://127.0.0.1:5001/api/v1"


def call(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    token: str | None = None,
    form: dict[str, str] | None = None,
) -> tuple[int, Any]:
    headers = {"Accept": "application/json"}
    body: bytes | None = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if form is not None:
        body = urllib.parse.urlencode(form).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return response.status, json.loads(raw) if raw.startswith(("{", "[")) else raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = raw
        return exc.code, parsed


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"[PASS] {message}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=DEFAULT_BASE, help="API base ending in /api/v1")
    parser.add_argument("--email", default="sara@carbonwise.demo")
    parser.add_argument("--password", default="User123!")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    try:
        status, payload = call(f"{base}/health")
        require(status == 200, "health endpoint returns 200")
        require(isinstance(payload, dict) and payload.get("data", {}).get("database") == "ok", "database reports ok")
        require(payload["data"].get("ai_model") == "openrouter/free", "AI model policy is openrouter/free")

        status, payload = call(
            f"{base}/auth/login",
            method="POST",
            payload={"email": args.email, "password": args.password},
        )
        require(status == 200, "demo user can log in")
        data = payload.get("data", {})
        token = data.get("access_token")
        require(bool(token), "login returns an access token")
        require(bool(data.get("refresh_token")), "login returns a refresh token")

        status, payload = call(f"{base}/auth/me", token=token)
        require(status == 200, "authenticated /auth/me works")
        require(payload.get("data", {}).get("user", {}).get("email") == args.email, "session belongs to the demo user")

        for path, label in (
            ("/categories", "catalog categories load"),
            ("/records", "records list loads"),
            ("/goals", "goals list loads"),
            ("/dashboard/summary", "dashboard summary loads"),
            ("/ai/status", "AI status loads"),
        ):
            status, payload = call(f"{base}{path}", token=token)
            require(status == 200, label)
            require("data" in payload, f"{label}: response uses the data envelope")

        status, payload = call(f"{base}/records")
        require(status == 401, "records rejects an anonymous request with 401")

        origin = base[:-7] if base.endswith("/api/v1") else base
        status, page = call(f"{origin}/admin/login")
        require(status == 200, "admin login page renders")
        require(isinstance(page, str) and "CarbonWise" in page, "admin login page contains the product name")

    except AssertionError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print("\nSmoke test passed. Base URL:", base)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
