# Backend — AI integration (OpenRouter)

## What it is

A backend-only client for OpenRouter `openrouter/free`, with prompt builders, JSON validation,
budget/rate limits, caching, usage metadata, and graceful fallbacks.

## Why it exists

The app needs grounded explanations and structured plans without exposing the API key or letting
the model invent emission numbers. The free router is the fixed provider policy.

## How it works

```
route → AiService → guard (auth, budget, rate, cache)
      → context builder (calculated values only)
      → OpenRouterClient (httpx)
      → validator/parser → usage row → response
```

Key files:

- `app/modules/ai/client.py` — httpx call, timeout, retries/backoff.
- `app/modules/ai/prompts.py` — system/user prompt templates.
- `app/modules/ai/validators.py` — JSON schemas + parsing.
- `app/modules/ai/services.py` — budget, rate limit, cache, context, usage.
- `app/modules/ai/repositories.py` — AI tables.
- `app/modules/ai/routes.py` — `/api/v1/ai/*`.

## Configuration

| Key | Default | Meaning |
|---|---|---|
| `OPENROUTER_API_KEY` | empty | backend only; AI disabled until set |
| `OPENROUTER_MODEL` | `openrouter/free` | fixed; startup guard |
| `AI_DAILY_TOKEN_BUDGET` | `200000` | global daily cap |
| `AI_RATE_LIMIT_PER_HOUR` | `20` | per-user cap |
| `AI_CACHE_TTL_MINUTES` | `60` | cache TTL |
| `AI_MAX_RETRIES` | `2` | retries on 429/5xx |
| `AI_REQUEST_TIMEOUT_SECONDS` | `45` | timeout |

## Request rules

- `temperature` low (e.g. 0.3); `max_tokens` at least 4096; reasoning capped at 1024.
- System prompt: use only provided values; never invent emissions/factors/savings; answer in the
  requested locale; return JSON only when a schema is requested.
- The context is server-built and contains no email/phone/full name/token.
- Vision: send the image only after consent; if the routed model rejects it, raise
  `vision_unavailable`.

## Responses

- Chat/summary: text; reject empty content.
- Insights/plan/alternatives/extraction: parse and validate JSON; one retry; typed error.
- Every response records `ai_usage` metadata and a disclaimer.
- No raw prompt text in logs.

## Fallbacks

- No key → `ai_disabled`; UI shows calculated data and a template plan/curated alternatives.
- 429 → `rate_limited`; retry with backoff, then friendly message.
- Malformed output → one retry, then `ai_invalid_output` and template fallback.
- Vision unavailable → `vision_unavailable` and manual entry.

## Testing

Mock `httpx`/`OpenRouterClient`; assert success, 429, timeout, empty content, malformed JSON,
vision unavailable, budget/rate/cache, and no network. `TestingConfig` blanks the key.

## Related

- ADR-0002
- Pages: [AI features](../ai-features.md), [API reference](../06-api-reference.md)
