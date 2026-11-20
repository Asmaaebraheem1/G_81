# 06 — API reference

Base: `/api/v1` — JSON only. Swagger UI: `/api/`. Admin pages are HTML at `/admin` and are
**not** part of this API.

## Auth

| Surface | Scheme |
|---|---|
| API | `Authorization: Bearer <access>`; refresh via `Authorization: Bearer <refresh>` on `/auth/refresh` |
| Admin | cookie session + CSRF (not part of this API) |

Access tokens live ~30 minutes; refresh tokens ~30 days and are rotated/revoked on logout.
The API rejects cookies. The admin panel rejects JWTs.

## Endpoints

### Public / catalog

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/health` | public | status, database, version |
| GET | `/categories` | public | active categories |
| GET | `/categories/{id}` | public | category detail |
| GET | `/factors?category_id=` | public | active factors, filterable |
| GET | `/factors/{id}` | public | factor detail + source |
| GET | `/alternatives` | public | curated alternatives |
| GET | `/alternatives/{id}` | public | alternative detail |
| GET | `/content/articles` | public | published articles |
| GET | `/content/articles/{slug}` | public | article detail |

### Auth / profile

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/auth/register` | public | create account + tokens |
| POST | `/auth/login` | public | access + refresh |
| POST | `/auth/refresh` | refresh | rotate refresh token |
| POST | `/auth/logout` | JWT | revoke refresh token |
| GET | `/auth/me` | JWT | current user + profile |
| PATCH | `/auth/me` | JWT | update name/locale/timezone |
| PATCH | `/auth/password` | JWT | change password |
| GET | `/profile` | JWT | profile detail |
| PATCH | `/profile` | JWT | profile/household preferences |
| GET | `/organization` | JWT (org) | organization detail |
| PATCH | `/organization` | JWT (org owner) | organization update |

### Consumption records

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/records` | JWT | list/search/filter records |
| POST | `/records` | JWT | create a record + calculate |
| GET | `/records/{id}` | JWT | record detail + formula |
| PATCH | `/records/{id}` | JWT | edit quantity/date/notes/factor |
| DELETE | `/records/{id}` | JWT | soft delete |
| GET | `/records/{id}/calculation` | JWT | formula breakdown |

Query: `page`, `per_page` (≤ 50), `q`, `category_id`, `from`, `to`, `sort` (`-activity_date`,
`activity_date`, `-emissions_grams`).

### Documents

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/documents` | JWT | multipart upload (image/PDF) |
| GET | `/documents` | JWT | list own documents |
| GET | `/documents/{id}` | JWT | metadata + extraction state |
| GET | `/documents/{id}/download` | JWT | authenticated file download |
| POST | `/documents/{id}/extract` | JWT | AI image extraction (best effort) |
| POST | `/documents/{id}/confirm` | JWT | validate confirmed values, create record |
| DELETE | `/documents/{id}` | JWT | delete unlinked document |

Upload constraints: JPG/PNG/WebP/PDF; 10 MB per file; 30 MB request; private storage.

### Dashboard, reports, export

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/dashboard/summary?period=month` | JWT | totals, category breakdown, goal progress |
| GET | `/reports/summary?period=month` | JWT | period report |
| GET | `/reports/trend?months=6` | JWT | monthly trend |
| GET | `/reports/categories?period=month` | JWT | category totals + shares |
| GET | `/reports/top-activities?period=month&limit=5` | JWT | highest-emission activities |
| GET | `/reports/comparison?period=month` | JWT | current vs previous period |
| GET | `/reports/export.csv?from=&to=` | JWT | CSV export |

### Goals

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/goals` | JWT | list goals |
| POST | `/goals` | JWT | create goal (baseline computed) |
| GET | `/goals/{id}` | JWT | goal detail |
| PATCH | `/goals/{id}` | JWT | edit title/date/status |
| DELETE | `/goals/{id}` | JWT | cancel/soft delete |
| GET | `/goals/{id}/progress` | JWT | current vs baseline/target |

### Reduction plans

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/plans` | JWT | list plans |
| POST | `/plans/generate` | JWT | AI structured plan (or template fallback) |
| GET | `/plans/{id}` | JWT | plan + actions |
| PATCH | `/plans/{id}` | JWT | status/title |
| PATCH | `/plans/{id}/actions/{action_id}` | JWT | action status |
| GET | `/plans/{id}/progress` | JWT | completion + estimated savings |

### Alternatives

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/alternatives/recommended` | JWT | personalized alternatives (AI + catalog) |
| GET | `/alternatives/saved` | JWT | saved/accepted alternatives |
| POST | `/alternatives/{id}/save` | JWT | save/accept/dismiss |

Body: `{ "status": "saved" | "accepted" | "dismissed" }`.

### Challenges, achievements, leaderboard

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/challenges` | JWT | active/upcoming/completed |
| GET | `/challenges/{id}` | JWT | detail + own progress |
| POST | `/challenges/{id}/join` | JWT | join |
| GET | `/challenges/{id}/progress` | JWT | progress + verification |
| POST | `/challenges/{id}/progress` | JWT | self-report/evidence action |
| GET | `/achievements` | JWT | badges, points, milestones |
| GET | `/leaderboard?period=month` | JWT | opt-in leaderboard |

### Notifications

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/notifications` | JWT | list (read/unread) |
| PATCH | `/notifications/{id}/read` | JWT | mark one read |
| POST | `/notifications/read-all` | JWT | mark all read |
| GET | `/notification-preferences` | JWT | per-type preferences |
| PATCH | `/notification-preferences` | JWT | update preferences |

### AI

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/ai/status` | JWT | enabled, model, vision best-effort |
| POST | `/ai/chat` | JWT | grounded assistant answer |
| GET | `/ai/conversations` | JWT | conversation list |
| GET | `/ai/conversations/{id}` | JWT | conversation messages |
| DELETE | `/ai/conversations/{id}` | JWT | delete conversation |
| POST | `/ai/insights` | JWT | report insights |
| POST | `/ai/summary` | JWT | sustainability summary |
| POST | `/ai/flag` | JWT | report an AI response |

## Request/response examples

### `POST /auth/register`

```json
{
  "email": "sara@example.com",
  "password": "StrongPass1!",
  "full_name": "Sara Demo",
  "account_type": "individual",
  "organization_name": null,
  "locale": "en",
  "timezone": "Europe/London"
}
```

Response `201`:

```json
{
  "data": {
    "user": { "id": 4, "email": "sara@example.com", "account_type": "individual", "locale": "en" },
    "access_token": "...",
    "refresh_token": "...",
    "token_type": "Bearer",
    "expires_in": 1800
  }
}
```

### `POST /auth/login`

```json
{ "email": "sara@example.com", "password": "StrongPass1!" }
```

Response `200` has the same token envelope. Wrong credentials → `401 invalid_credentials`.

### `POST /auth/refresh`

Header: `Authorization: Bearer <refresh_token>`. Response `200` returns a new access + refresh
token pair; the old refresh token is revoked.

### `POST /records`

```json
{
  "category_id": 1,
  "factor_id": 1,
  "activity_date": "2026-06-15",
  "quantity": 120.5,
  "unit": "kWh",
  "notes": "June electricity"
}
```

Response `201`:

```json
{
  "data": {
    "id": 61,
    "category": { "id": 1, "name_en": "Electricity", "name_ar": "الكهرباء" },
    "quantity": "120.5000",
    "unit": "kWh",
    "factor_grams_co2e_snapshot": 233,
    "factor_source_snapshot": "Example grid factor (2025)",
    "emissions_grams": 28077,
    "emissions_kg": 28.08,
    "formula": "120.5 kWh × 233 g CO2e/kWh = 28,077 g CO2e (28.08 kg)"
  }
}
```

### `POST /documents` (multipart)

Fields: `file` (required), `organization_id` (optional, org users), `consent` (`true` required for
AI extraction). Response `201` with document metadata and status `uploaded`.

### `POST /documents/{id}/extract`

Response `200`:

```json
{
  "data": {
    "status": "extracted",
    "model": "free-model-returned",
    "fields": {
      "vendor": "City Electric",
      "billing_period": "2026-05",
      "consumption_value": 120.5,
      "unit": "kWh",
      "confidence": 0.82
    }
  }
}
```

If the routed model has no vision: `422 vision_unavailable` with a manual-entry fallback.
Extraction never creates a record. Confirmation does.

### `POST /documents/{id}/confirm`

```json
{
  "vendor": "City Electric",
  "activity_date": "2026-05-31",
  "category_id": 1,
  "factor_id": 1,
  "quantity": 120.5,
  "unit": "kWh",
  "notes": "Confirmed from bill"
}
```

Response `201` with the created record and formula. The document becomes `confirmed`.

### `POST /ai/chat`

```json
{ "message": "Why did my emissions go up this month?", "conversation_id": null, "locale": "en" }
```

Response `200`:

```json
{
  "data": {
    "conversation_id": 12,
    "message_id": 34,
    "content": "Your calculated emissions rose ...",
    "model": "free-model-returned",
    "context": { "period": "2026-06", "total_kg": 184.2, "top_category": "Electricity" },
    "disclaimer": "AI explanation of backend-calculated values. Estimates only."
  }
}
```

If AI is disabled: `503 ai_disabled` with a friendly message and calculated fallback data.

### `POST /ai/insights`

```json
{ "period": "month", "from": "2026-06-01", "to": "2026-06-30", "locale": "en" }
```

Response `200` with validated structured fields: `top_sources`, `changes`, `comparisons`,
`opportunities`, `narrative`, `calculated_context`. Numeric fields are copied from backend
calculations, not generated by the model.

### `POST /ai/flag`

```json
{ "message_id": 34, "reason": "inaccurate", "notes": "It said my total was different." }
```

Response `201` with a flagged-response row for admin review.

## Errors

```json
{ "error": { "code": "invalid_credentials", "message": "...", "details": {} } }
```

| Code | HTTP | When |
|---|---|---|
| `validation_error` | 422 | field errors |
| `invalid_credentials` | 401 | wrong email/password |
| `token_expired` | 401 | expired JWT |
| `token_revoked` | 401 | revoked refresh |
| `forbidden` | 403 | wrong owner/role |
| `not_found` | 404 | missing/unauthorized resource |
| `conflict` | 409 | duplicate email/slug, state conflict |
| `account_inactive` | 403 | suspended user/admin |
| `rate_limited` | 429 | AI or login rate limit |
| `ai_disabled` | 503 | no API key / feature off |
| `vision_unavailable` | 422 | routed free model lacks image support |
| `ai_invalid_output` | 502 | model returned malformed structured output |
| `upload_too_large` | 413 | file/request cap exceeded |
| `unsupported_file_type` | 422 | MIME/content mismatch |
| `internal_error` | 500 | unexpected |

## Conventions

- List endpoints: `?page=&per_page=&q=&sort=`, `per_page` ≤ 50.
- Success: `{ "data": ... }`; list: `{ "data": [...], "meta": { page, per_page, total, pages } }`.
- All input validated with pydantic v2 (`extra="forbid"`).
- Dates: ISO `YYYY-MM-DD`; timestamps: UTC ISO 8601 with `Z`.
- Emissions: `emissions_grams` integer + `emissions_kg` formatted string.
- AI responses always include a disclaimer and are visibly separate from calculated values.
- CSV export: `text/csv; charset=utf-8`, `Content-Disposition: attachment`.
- No secrets or stack traces in responses.

Related: #6, #7, #8
