# Backend — error handling

## What it is

Central error handlers that turn exceptions into a consistent JSON envelope for `/api/v1` and a
safe HTML error page for `/admin`.

## Why it exists

Clients need stable error codes; the UI needs friendly messages; logs need context without leaking
secrets or stack traces.

## Error envelope

```json
{ "error": { "code": "validation_error", "message": "Invalid input", "details": {} } }
```

## Status/code map

| Code | HTTP | When |
|---|---|---|
| `validation_error` | 422 | pydantic/field errors |
| `invalid_credentials` | 401 | wrong email/password |
| `token_expired` | 401 | expired JWT |
| `token_revoked` | 401 | revoked refresh |
| `forbidden` | 403 | wrong owner/role |
| `not_found` | 404 | missing/unauthorized resource |
| `conflict` | 409 | duplicate/state conflict |
| `account_inactive` | 403 | suspended account |
| `rate_limited` | 429 | login/AI rate limit |
| `ai_disabled` | 503 | no key |
| `vision_unavailable` | 422 | no image support |
| `ai_invalid_output` | 502 | malformed model JSON |
| `upload_too_large` | 413 | file/request cap |
| `unsupported_file_type` | 422 | MIME mismatch |
| `internal_error` | 500 | unexpected |

## Rules

- Known domain errors use `ApiError(code, message, status, details)`.
- Unexpected exceptions are logged with a request id; the client gets `internal_error`.
- Admin gets an HTML error page with the same request id; no stack trace.
- Never log tokens, passwords, API keys, prompts, or uploaded file contents.
- AI/provider errors are mapped to typed codes; no raw provider response is returned.

## Testing

Tests assert the envelope, status, code, and that no stack trace/secret appears in the response.
`tests/core/test_errors.py` covers the central handlers.

## Related

- Pages: [API](api.md), [AI integration](ai-integration.md)
