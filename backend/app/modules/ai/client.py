"""OpenRouter client. The key lives only on the backend."""

from __future__ import annotations

import time

import httpx
from flask import current_app

from app.modules.ai.errors import AiUnavailable

DISCLAIMER = (
    "AI explanation of backend-calculated values. Estimates only; not professional "
    "environmental, financial, or legal advice."
)


def is_enabled() -> bool:
    return bool(current_app.config.get("OPENROUTER_API_KEY")) and not current_app.config.get(
        "TESTING"
    )


def model_name() -> str:
    return current_app.config.get("OPENROUTER_MODEL", "openrouter/free")


def _headers() -> dict[str, str]:
    key = current_app.config.get("OPENROUTER_API_KEY", "")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "CarbonWise",
    }


def _map_http_error(status: int, body: str) -> AiUnavailable:
    lower = (body or "").lower()
    if status in {400, 404, 422} and any(
        word in lower for word in ("image", "vision", "modality", "multimodal")
    ):
        return AiUnavailable(
            "vision_unavailable",
            "The routed free model cannot read images right now. Enter the values manually.",
            422,
        )
    if status == 402:
        return AiUnavailable(
            "ai_budget_exhausted",
            "The free AI budget is exhausted. Backend calculations are still available.",
            503,
        )
    if status == 429:
        return AiUnavailable(
            "rate_limited",
            "The free AI router is rate-limited. Try again shortly.",
            429,
        )
    if status == 401 or status == 403:
        return AiUnavailable(
            "ai_disabled",
            "AI is not available with the current provider configuration.",
            503,
        )
    if status >= 500:
        return AiUnavailable(
            "ai_unavailable",
            "The free AI router is temporarily unavailable.",
            503,
        )
    return AiUnavailable(
        "ai_request_failed",
        "The AI request could not be completed.",
        502,
    )


def chat_completion(
    messages: list[dict],
    *,
    temperature: float = 0.2,
    max_tokens: int = 900,
    response_format: dict | None = None,
) -> dict:
    """Call the OpenRouter free router once, with bounded retries."""
    if not is_enabled():
        raise AiUnavailable(
            "ai_disabled",
            "AI is disabled because no OpenRouter key is configured. "
            "All calculated features still work.",
            503,
        )
    url = (
        current_app.config.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
        + "/chat/completions"
    )
    payload: dict = {
        "model": model_name(),
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        payload["response_format"] = response_format
    attempts = max(0, int(current_app.config.get("AI_MAX_RETRIES", 2))) + 1
    timeout = httpx.Timeout(float(current_app.config.get("AI_REQUEST_TIMEOUT_SECONDS", 45)))
    last_error: AiUnavailable | None = None
    for attempt in range(attempts):
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, headers=_headers(), json=payload)
        except httpx.TimeoutException as exc:
            last_error = AiUnavailable(
                "ai_timeout",
                "The free AI router timed out. Please try again.",
                504,
            )
            if attempt < attempts - 1:
                time.sleep(0.4 * (attempt + 1))
                continue
            raise last_error from exc
        except httpx.HTTPError as exc:
            last_error = AiUnavailable(
                "ai_unavailable",
                "The free AI router could not be reached.",
                503,
            )
            if attempt < attempts - 1:
                time.sleep(0.4 * (attempt + 1))
                continue
            raise last_error from exc
        if response.status_code >= 400:
            error = _map_http_error(response.status_code, response.text[:2000])
            if response.status_code in {429, 500, 502, 503, 504} and attempt < attempts - 1:
                last_error = error
                time.sleep(0.4 * (attempt + 1))
                continue
            raise error
        try:
            body = response.json()
        except ValueError as exc:
            raise AiUnavailable(
                "ai_invalid_output", "The AI provider returned non-JSON data.", 502
            ) from exc
        choices = body.get("choices") or []
        if not choices:
            raise AiUnavailable(
                "ai_invalid_output", "The AI provider returned an empty response.", 502
            )
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
        if not content or not str(content).strip():
            raise AiUnavailable(
                "ai_invalid_output", "The AI provider returned an empty message.", 502
            )
        return {
            "content": str(content).strip(),
            "model": body.get("model") or model_name(),
            "usage": body.get("usage") or {},
        }
    raise last_error or AiUnavailable(
        "ai_unavailable", "The free AI router is temporarily unavailable.", 503
    )
