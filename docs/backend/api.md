# Backend — API conventions

## What it is

The JSON API is served under `/api/v1` by Flask blueprints and documented with
`flask-openapi3` + pydantic v2. Swagger UI is at `/api/`.

## Why it exists

The Flutter app needs a stable, versioned contract with consistent envelopes, auth, pagination,
and validation errors. The OpenAPI spec is the source of truth for endpoint shapes.

## Response envelope

Success:

```json
{ "data": { "...": "..." } }
```

List:

```json
{ "data": [], "meta": { "page": 1, "per_page": 20, "total": 0, "pages": 0 } }
```

Error:

```json
{ "error": { "code": "validation_error", "message": "Invalid input", "details": {} } }
```

## Rules

- JSON only; no cookies on `/api`.
- `Authorization: Bearer <access>` for protected routes.
- Pydantic v2 models with `extra="forbid"`; validate before services.
- Pagination on every list: `page`, `per_page` (≤ 50), `q`, `sort`.
- Dates ISO `YYYY-MM-DD`; timestamps UTC ISO 8601.
- Emissions as integer `emissions_grams` + formatted `emissions_kg`.
- Errors use the central handlers; no stack traces.
- AI endpoints include a disclaimer and a `calculated_context` block.

## Example

```cmd
curl.exe -H "Authorization: Bearer <token>" http://127.0.0.1:5000/api/v1/records
```

## Testing

API tests use the Flask test client with a temporary SQLite DB and assert status, envelope,
validation, ownership, and auth. See `docs/06-api-reference.md`.

## Related

- Pages: [authentication](authentication.md), [error handling](error-handling.md), [API reference](../06-api-reference.md)
