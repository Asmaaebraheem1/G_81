# 04 — Architecture

## Backend

```
route / Jinja view → service → repository → SQLite
```

- `create_app(config)` builds the app; no import-time side effects.
- Blueprints per module; `/api/v1` for JSON, `/admin` for Jinja.
- Services own business rules and transactions.
- Repositories own all SQLAlchemy access.
- `core/` owns config, db, errors, security, logging, responses.

### Request flow

1. Route validates input (pydantic / form).
2. Service checks rules + permissions, calls repositories.
3. Repository reads/writes SQLite.
4. Service commits/rolls back.
5. Route returns the standard envelope.

### Error contract

```json
{ "error": { "code": "snake_case", "message": "Human message", "details": {} } }
```

- 400 validation / 401 auth / 403 permission / 404 missing / 409 conflict / 422 field errors /
  429 rate limit / 500 unexpected.
- No stack traces or internals to clients.
- Admin panel gets an HTML error page; API gets JSON.

### Auth split

| Surface | Auth |
|---|---|
| `/api/v1` | JWT access + refresh (`Authorization: Bearer`) |
| `/admin` | signed-cookie session + CSRF |

Never mix: the API rejects cookies, the admin rejects JWTs.

### Modules

| Module | Responsibility |
|---|---|
| `auth` | register/login/refresh/logout, password hashing, JWT |
| `users` | profile, settings, account type, household info |
| `organizations` | organization profile and ownership |
| `catalog` | emission categories and factors, public reads, admin CRUD |
| `records` | consumption records, calculation engine, snapshots |
| `documents` | private uploads, extraction state, confirmation |
| `reports` | aggregates, trends, comparisons, CSV export |
| `goals` | percentage reduction goals, baselines, progress |
| `plans` | reduction plans, actions, progress |
| `alternatives` | catalog, personalization, saved alternatives |
| `challenges` | challenges, participation, badges, points, leaderboard |
| `notifications` | in-app notifications, preferences, summaries |
| `ai` | OpenRouter client, prompts, validation, usage, flags |
| `content` | bilingual educational articles |
| `admin` | Jinja login/shell/dashboard/management, audit log |

## Mobile

```
widget → BLoC event → use case → repository → Dio / sqflite
```

- Feature-first: `data/`, `domain/`, `presentation/`.
- One `ApiClient` (Dio) with auth, refresh-once, error mapping, debug-only logging.
- One `AppDatabase` (sqflite) with versioned migrations; cache only.
- BLoC emits explicit `initial/loading/success/failure` states.
- No Dio/sqflite calls from widgets.

### Feature dependency order

`auth → profile → catalog → records → documents → reports → goals → plans/alternatives →
challenges/notifications → AI → admin`.

AI is last because it needs real calculated data.

## Main flow — add a consumption record

1. App loads categories/factors from `/api/v1/categories`.
2. User selects category/factor, quantity, unit, date.
3. `POST /api/v1/records` with JWT.
4. Route validates pydantic input; service loads the active factor.
5. Service snapshots factor value/source, computes `emissions_grams = round(quantity × factor_grams)`,
   saves the record, commits.
6. API returns the record + formula breakdown.
7. BLoC emits `RecordSaved`; dashboard/report caches invalidate; UI shows the new total.

## Main flow — bill upload and confirmation

1. App uploads image with consent → `POST /api/v1/documents`.
2. Backend validates MIME/size, stores privately, creates `documents` row.
3. User requests extraction → `POST /api/v1/documents/{id}/extract`.
4. Backend calls OpenRouter `openrouter/free` with the image; if the routed model has no vision,
   returns `vision_unavailable`; UI falls back to manual entry.
5. Backend stores candidate JSON + model; does **not** create a record.
6. User confirms/corrects → `POST /api/v1/documents/{id}/confirm`.
7. Backend validates confirmed values, maps them to a factor, creates a record with a factor
   snapshot, links the document, commits.
8. UI shows the calculated result and the formula.

## AI flow

```
app → /api/v1/ai/... → auth → guard (rate/budget/cache)
    → server-built context (calculated values only)
    → OpenRouter openrouter/free → validate/parse → persist usage
    → response → BLoC → UI (labelled AI, never mixed with calculated values)
```

- The backend builds the context; the model never queries the database.
- Structured outputs use a JSON schema; invalid output → one retry → typed error/fallback.
- `ai_usage` records metadata only; no raw prompt logging with personal data.
- Reported responses are stored after PII redaction for admin review.

## Security

- Passwords hashed; JWT in `flutter_secure_storage`; no secrets in logs.
- Admin CSRF on every form; autoescaping on; `|safe` banned.
- Parameterized SQL only; least-privilege queries.
- Uploads: MIME/size validation, generated filenames, private storage, authenticated download,
  no execution, no directory listings.
- AI: backend-only key, consent before image upload, no prompt logging, budget/rate limits.
- Admin audit log for sensitive changes.
- SQLite `PRAGMA foreign_keys=ON` and WAL mode on every connection.

Related: #2, #5
