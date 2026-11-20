# agent.md — Project Rules (CarbonWise)

This file is the **single source of truth** for how work is done in this repository.
Read it fully before any task. If a request conflicts with these rules, **stop and ask** — do not silently break a rule.

> Status: rules v1 — generated for **CarbonWise** (`carbonwise`) on 2026-11-19.
> Items marked **[PENDING]** are not decided yet and must not be assumed.

---

## 1. Fixed stack (non-negotiable)

| Layer | Decision |
|---|---|
| Mobile app | **Flutter** (stable channel), Android |
| Mobile state management | **BLoC** (`flutter_bloc`) — no other state-management library |
| Mobile HTTP client | **Dio** |
| Mobile local persistence | **SQLite** (`sqflite`) — offline cache only |
| Mobile models | `freezed` + `json_serializable` (codegen) |
| Mobile routing | `go_router` |
| Mobile secure storage | `flutter_secure_storage` for tokens only |
| Backend language | **Python 3.15** |
| Backend framework | **Flask** |
| Backend templates | **Jinja2** (server-rendered admin panel) |
| Backend environment | **venv** at `backend/.venv`, pip + pinned `requirements.txt` |
| Database | **SQLite ONLY** — backend and app |
| ORM / migrations | SQLAlchemy 2.x + Flask-SQLAlchemy + Flask-Migrate (Alembic) |
| API docs | `flask-openapi3` + pydantic v2 (Swagger at `/api/`) |
| API auth | JWT access + refresh (`Flask-JWT-Extended`) |
| Admin auth | Signed-cookie session + CSRF (`Flask-WTF`) |
| AI provider | **OpenRouter `openrouter/free` only** |
| Languages | **English + Arabic (RTL)** in the app; docs in English |
| Shell (this repo) | **Windows `cmd` (Command Prompt)** — PowerShell/bash syntax is NOT allowed |

### 1.1 Hard "never" list (database)

Never introduce another database or database-like store, in the backend **or** the app, including:
PostgreSQL, MySQL/MariaDB, MongoDB, Redis, Firebase/Firestore, Supabase, Hive, Isar, Drift,
ObjectBox, Realm, `shared_preferences` as a database, or any cloud database.

If a feature seems to need one, stop and ask the owner first.

---

## 2. Repository layout

```
G_81/                         # CarbonWise repository root
├── agent.md                  # this file (rules — how we work)
├── AGENTS.md                 # auto-loaded pointer to agent.md
├── INTAKE.md                 # approved Phase 0 intake
├── docs/                     # project documentation (multi-file — see §9)
├── .pi/
│   └── skills/               # agent skills (workflows that must be followed)
├── .github/                  # workflows + issue/PR templates
├── scripts/                  # local verification and demo scripts
├── backend/                  # Flask + Jinja + SQLite
└── mobile/                   # Flutter + BLoC + Dio + SQLite
```

- Backend and mobile are separate, independent projects (separate dependency files, separate test runs).
- No shared code between them except the API contract.
- Folder names are **`backend/`** and **`mobile/`**.

---

## 3. Backend rules (Flask)

### 3.1 Environment
- A venv lives at `backend/.venv`. Every command runs through it (`.venv\Scripts\python.exe`).
- **pip + `requirements.txt`** only. Exact pinned versions in `requirements.txt`; dev/test tooling in `requirements-dev.txt`.
- Never install packages globally. Never commit `.venv/`.
- Python target: **3.15**.
- Every command documented or run in this repo is **`cmd` syntax**, e.g.
  `cd backend` → `.venv\Scripts\activate` → `pip install -r requirements.txt` → `python -m pytest --cov`.

### 3.2 Modular architecture (mandatory)
- **Application factory** pattern (`create_app(config)`) — no global `app` object doing work at import time.
- **Blueprints** for routing, split by module/feature.
- **Layered flow, one direction only:**

  ```
  route / jinja view  →  service  →  repository  →  SQLite
  ```

  - Routes/views: HTTP only (parse input, call service, build response). **No SQL, no business rules.**
  - Services: business logic, orchestration, transactions.
  - Repositories: the **only** place that talks to the database.
  - Jinja templates: presentation only — no business logic, no SQL, no data access.
- Shared concerns in `core/`: config, db connection, error handlers, logging, security helpers.
- Cross-module imports only through public module interfaces.

Structure:

```
backend/
├── .venv/
├── app/
│   ├── __init__.py            # create_app()
│   ├── core/                  # config, db, errors, logging, security
│   ├── modules/
│   │   └── <feature>/
│   │       ├── routes.py      # API endpoints (blueprint)
│   │       ├── models.py      # SQLAlchemy models
│   │       ├── services.py
│   │       ├── repositories.py
│   │       └── validators.py
│   ├── api/                   # /api/v1 registration
│   ├── templates/             # Jinja2 (admin panel)
│   └── static/
├── migrations/                # Alembic (Flask-Migrate)
├── tests/
└── requirements.txt
```

### 3.3 SQLite rules
- Exactly **one** database file, path from config (not hardcoded).
- One central connection/factory — never open ad-hoc connections in random files.
- `PRAGMA foreign_keys = ON` on every connection; WAL mode enabled.
- **Parameterized queries only.** Never build SQL with f-strings/`%`/`.format()` from user input.
- **Access layer: SQLAlchemy 2.x ORM on SQLite** (`Flask-SQLAlchemy`), with **`Flask-Migrate` / Alembic** for schema migrations. Raw `sqlite3` is allowed only for PRAGMAs/edge cases.
- Schema changes are versioned with Alembic migrations — never edit a live schema by hand.
- Foreign keys and indexes declared explicitly; `PRAGMA foreign_keys=ON` enforced for every connection.
- Models live beside their module (`modules/<feature>/models.py`); **session commit/rollback belongs to services**.
- Startup guard: reject any `DATABASE_URL` that does not start with `sqlite:`.
- Startup guard: reject any `OPENROUTER_MODEL` other than `openrouter/free`.

### 3.4 Jinja2 (admin panel)
- The Jinja side is the **admin / back-office panel**, protected by **session cookies**. It must never accept a JWT; the JSON API must never accept a cookie.
- Every admin view requires login (`login_required`); all forms are CSRF-protected (`Flask-WTF`).
- Passwords hashed with `werkzeug.security` (or Argon2) — never stored or logged in clear text.
- Sessions stay stateless (signed cookies, no Redis). If revocation is needed, store session rows **in SQLite**.
- All pages extend a `base.html` layout; use blocks, not copy-paste.
- Autoescaping stays ON. `|safe` is banned unless explicitly reviewed.
- URLs via `url_for(...)`, never hardcoded paths.
- CSS/JS in `static/`, no heavy inline scripts, no CDN required for the demo.
- The HTML panel and the JSON API share the same services.
- Admin UI is English in v1; admin forms edit both `*_en` and `*_ar` content fields.

### 3.5 API rules
- JSON only, versioned prefix: `/api/v1/...`.
- Consistent response shape and error shape (single helper for success and errors).
- Correct HTTP status codes (200/201/204, 400/401/403/404/409/422, 500).
- All input validated server-side before services (pydantic v2).
- Central error handlers — no stack traces or internals leaked to clients.
- Auth: **JWT** — short-lived access + refresh token, `Authorization: Bearer <token>`.
- API documentation: **OpenAPI 3** via **`flask-openapi3`** (pydantic v2 models) with Swagger UI at `/api/`; spec generated from route modules.
- Config/secrets from environment / `.env`; `.env.example` committed, `.env` never committed.
- Pagination + filtering on every list endpoint.

### 3.6 Backend dependencies
- Core: `Flask`, `python-dotenv`, `Flask-SQLAlchemy`, `Flask-Migrate`, `SQLAlchemy` 2.x, `flask-openapi3` + `pydantic` v2, `Flask-JWT-Extended`, `Flask-WTF`, `httpx`, `Pillow`, `email-validator`.
- Dev/test: `pytest`, `pytest-cov`, `ruff`, `black`.
- Any new dependency must be justified and agreed before adding.

---

## 4. Flutter rules

### 4.1 Structure — feature-first
```
mobile/lib/
├── main.dart
├── app/                  # app widget, router, theme, DI, l10n
├── core/                 # config, network, database, error, utils
└── features/<feature>/
    ├── data/             # dto/models, remote datasource (Dio), local datasource (sqflite), repository impl
    ├── domain/           # entities, repository contracts, use cases
    └── presentation/     # bloc, pages, widgets
```

### 4.2 BLoC
- `flutter_bloc` only. One BLoC per feature/screen concern.
- States/entities immutable via **`freezed`** + `json_serializable`; no hand-written `copyWith`/`==`/`hashCode`.
- Every state is explicit: `initial`, `loading`, `success`, `failure` (+ feature-specific).
- BLoC handles events → use cases → repositories. UI emits events and renders states; **no business logic in widgets**.
- No `setState` for business state; local-only UI state is acceptable.
- No direct Dio/sqflite calls from widgets or BLoCs.

### 4.3 Dio
- **One** configured `Dio` instance (`ApiClient`) with interceptors: base URL, headers, auth token, logging (debug only), error mapping, timeouts.
- Base URL/keys from build config (`--dart-define`), never hardcoded.
- Map Dio errors to app-level failures; never leak raw exceptions to the UI.
- Cancel tokens for requests that can outlive their screen.

### 4.4 SQLite (sqflite)
- The app has its **own local SQLite database**, used as an offline cache; the backend remains authoritative.
- One database helper: single creation path, versioned `onCreate`/`onUpgrade`.
- Repository pattern hides SQLite from the rest of the app.
- Run non-trivial DB work off the UI isolate.
- Migrations preserve user data (no drop-and-recreate unless agreed).

### 4.5 Quality
- `flutter analyze` must report **zero** issues; `dart format` applied before every commit.
- Lint ruleset: **`flutter_lints`** + `analysis_options.yaml` strict rules (`strict-casts`, `strict-inference`, `strict-raw-types`). `// ignore` only with a written reason.
- Null safety respected, no `dynamic` leakage in models, no `!` to silence analyzers.
- No unused code, no commented-out blocks.

### 4.6 Auth storage & security
- JWT access + refresh tokens stored in **`flutter_secure_storage`** (Android Keystore / iOS Keychain). Not in sqflite, not in `shared_preferences`, not in logs.
- Token attach + refresh happen in a Dio interceptor: on `401`, refresh once, retry the original; refresh failure → logout and clear storage.
- No secrets, tokens, prompt contents, or personal data in any log/crash report.

### 4.7 Localization (EN + AR, always)
- All user-facing strings in ARB files (`app_en.arb`, `app_ar.arb`), generated via `flutter gen-l10n`.
- Arabic layout is RTL; test both directions on every screen.
- No hardcoded user-facing strings in widgets.
- Dates/numbers/currency formatted with `intl`.
- Language switcher persisted via `flutter_secure_storage` or the local settings table.
- AI responses are requested in the user's locale; stored AI text is labelled with its locale.

---

## 5. AI integration (OpenRouter, free models)

- **Free models only**, always. Paid models are forbidden, even as fallback.
- **Model: `openrouter/free` only** — OpenRouter's Free Models Router. It picks among free models itself.
- **No fallback model.** On failure/429, surface a clear error and retry the same model with backoff.
- The model ID lives in config: `OPENROUTER_MODEL=openrouter/free` in `.env` / `.env.example`.
- Key comes only from `.env` (`OPENROUTER_API_KEY`) on the backend; never committed, logged, or sent to the app.
- Until a key exists, the AI module is developed and tested against a **mocked** client.
- The Flutter app never holds the key and never calls OpenRouter directly — it calls our backend.
- Handle rate limits (429), timeouts, empty responses, and outages: bounded retries with backoff, clear user-facing error, no infinite retries.
- **Lifecycle:** set a completion-token floor (4096) and cap hidden reasoning (1024); reject empty content as a typed error.
- Prompts/model names live in config/constants, not scattered through code.
- Never log prompts/responses containing personal data in production.
- All AI calls are mocked in tests — no real network calls in the test suite.
- Add a daily token budget, hourly rate limit, prompt-hash cache, and an `ai_usage` record per call.
- **Vision is best-effort:** only when the routed free model supports image input. If not, return `vision_unavailable` and fall back to manual entry. Never use a paid vision model.
- **No invented numbers:** the backend injects calculated values; AI may explain them but never supplies emission values or estimated savings. AI never writes directly to the database.
- **Consent:** before sending a bill image to the free router, show a clear consent notice. Manual entry is always available.
- **Monitoring:** store usage metadata (feature, model returned, tokens, latency, status). Do not store raw prompts containing personal data. Reported responses may be stored after PII redaction for admin review.

---

## 6. Testing rules

### 6.1 Minimum coverage: **50%**
- Enforced on **both** backend and mobile.
- Backend: `pytest --cov` with `--cov-fail-under=50`.
- Mobile: `flutter test --coverage`, checked against 50% (lcov).
- Coverage is measured per side, not combined. Below 50% = the work is not done.
- Genuinely untestable lines need `# pragma: no cover` with a comment.

### 6.2 All testing types
**Backend**
- Unit tests (services, repositories, validators).
- Integration tests (Flask test client + real temp SQLite DB).
- API/contract tests (status codes, shapes, auth, validation).
- Tests isolated: fresh temporary SQLite per test/session, no shared state, no network.

**Flutter**
- Unit tests (BLoC via `bloc_test`, repositories, mappers).
- Widget tests (screens render correct states).
- Integration/E2E tests (`integration_test`) for main flows.

**Cross-cutting**
- Every BLoC emits the expected sequence on success and failure.
- Every endpoint has a happy-path and an error-path test.
- Manual smoke test before "done".
- CI fails on test failure or coverage below 50%.

### 6.3 Rules of writing tests
- External services (OpenRouter, network) always mocked/faked.
- Test names describe behaviour, not implementation.
- No tests that only assert "no exception".
- Bug fix → failing test first, then fix.

---

## 7. Code style & conventions

- **Python:** PEP 8, `ruff` + `black`, 100-char lines, type hints on public functions, docstrings, `snake_case`/`PascalCase`.
- **Dart:** Effective Dart, `dart format`, 80-char lines, `snake_case` files, `PascalCase` classes, `camelCase` members.
- **SQL:** `snake_case`, plural table names, explicit `id` PK, `created_at`/`updated_at`, named FKs.
- **Commits/branches/PRs:** Conventional Commits + `dev/<issue>-<slug>` + one PR per issue (§8).
- **Comments:** explain *why*, not *what*. No dead code, no `TODO` without an owner/issue.

---

## 8. Git & GitHub workflow

**Skill: `.pi/skills/github-workflow/SKILL.md` — read it before any branch/issue/PR work.**

### 8.1 Branches
- `main` — the only long-lived branch. Always releasable, always green. **No direct commits, no force-push.**
- `dev/<issue-number>-<kebab-slug>` — one branch per issue, from `main`, deleted after merge.

### 8.2 Issues
- **Every** edit or feature starts with a GitHub issue — no issue, no work.
- The issue must contain: context/why, goal, scope, numbered acceptance criteria, task checklist, test plan, out of scope, docs to update, references.
- **Big feature → split**: one epic + small child issues (`Part of #<epic>`), each independently shippable with its own branch/PR.
- Issues are created with `gh issue create` using the template in the skill's `references/`.

### 8.3 Linking (mandatory)
- Branch name contains the issue number.
- PR body ends with `Closes #<n>` (children: `Part of #<n>`).
- Issue updated with branch + PR link as soon as the PR exists.

### 8.4 Commits & PRs
- Conventional Commits with `Refs #<n>` in the footer.
- One PR per issue, draft until review passes, titled like the issue.
- Never commit secrets, `.env`, `.venv/`, build artefacts.

### 8.5 Merge policy
- Push to the PR branch **only after** owner confirmation (unless yoyo is on).
- Merge to `main` only when: tests pass, coverage ≥ 50%, docs updated, review done, CI green, owner approved.
- Default: squash merge + delete branch. The agent merges after approval and green checks.

---

## 9. Documentation (`docs/`)

**Skill: `.pi/skills/project-docs/SKILL.md`.**

- `docs/` is the source of truth for **what the project is and how it works**; `agent.md` is the source of truth for **how we work**.
- Multi-file, Laravel-style, organized by topic, with `docs/README.md` as the index.
- Two audiences: a new human developer and an AI agent. Exact paths, real `cmd` commands, current code samples.
- Documentation is **part of done**: update affected pages in the same PR.
- Architecture decisions get an ADR in `docs/decisions/`.
- `docs/status.md` = current state; `docs/changelog.md` = history with issue links.
- `docs/demo-script.md` = the client demo path, logins, expected output, fallbacks.
- `docs/ai-features.md` = every AI feature, input/output/model/modality/limitations.
- `docs/diagrams/` = the five black-and-white system analysis diagrams.
- `docs/screenshots/` = the complete mobile and admin screenshot library.
- `docs/assets/` = visual asset index and credits.

---

## 10. Development process (mandatory order)

| # | Step | Mode | Gate |
|---|---|---|---|
| 1 | **Planning** | normal | plan shown; ambiguities asked |
| 2 | **Create issue** | normal | issue complete, split if big |
| 3 | **Create PR** | normal | branch from `main`, draft PR linked |
| 4 | **Documentation** | yoyo | docs describe the target state |
| 5 | **Coding** | yoyo | compiles, analyzer/linter clean |
| 6 | **Testing** | yoyo | tests pass, coverage ≥ 50% |
| 7 | **Review** | normal | owner confirms (or yoyo) |
| 8 | **Push** | normal | commits to the PR branch only |
| 9 | **Merge** | normal | checks green + approval |

Rules:
- Steps 4–6 run in **yoyo mode**: the owner may be away, so **do not ask questions** — decide the obvious, act end-to-end, report decisions at review. Never invent product requirements.
- Questions belong in Planning/Issue or in the review.
- The agent **never pushes** before review confirmation (unless the owner explicitly said "go"), and **never merges** without green checks.
- If a step reveals the issue was wrong, fix the issue first.
- The owner approved the intake with "continue"; for this build, the agent may proceed through the approved plan and report at phase/feature gates.

---

## 11. Behaviour contract

1. Read this file first; keep it updated when a rule changes.
2. **Plan before coding** on anything bigger than a single file.
3. **Ask before:** adding a dependency outside the stack, changing architecture, destructive schema changes, deleting files, rewriting large areas, `git push`, or anything irreversible.
4. Never invent requirements. If unclear, ask.
5. Never break the fixed stack: Flutter + BLoC + Dio + sqflite / Flask + Jinja + SQLite / OpenRouter free.
6. Report what changed, where, and how it was tested (commands + coverage).
7. **Shell is `cmd`.** Every command must work in Command Prompt.
8. Keep the repo clean: no secrets, no build artefacts, `.gitignore` maintained.
9. Prefer the framework's official/recommended structure.
10. **Follow the skills.** Before relevant work, read the matching `SKILL.md`. If a needed procedure is missing, create it first.
11. Keep AI-generated text visibly separate from backend-calculated values.
12. Never log tokens, API keys, prompts, or personal data.

### Skills registry

| Skill | Path | When it applies |
|---|---|---|
| `github-workflow` | `.pi/skills/github-workflow/` | Any change: issue → branch → PR gates |
| `project-docs` | `.pi/skills/project-docs/` | Any change affecting documented reality |
| `skill-authoring` | `.pi/skills/skill-authoring/` | New repeated procedure; rule changes |

---

## 12. Product scope (CarbonWise)

- **Idea:** CarbonWise is an AI-assisted sustainability platform for individuals, households, and organizations. It tracks consumption, calculates estimated emissions from documented factors, produces reports and goals, and uses OpenRouter (`openrouter/free`) for a grounded assistant, insights, reduction plans, alternatives, and best-effort bill extraction. A Flask/Jinja admin dashboard manages the platform.
- **Actors:** Guest, individual/household user, organization user, administrator (`super_admin`, `content_editor`).
- **Payments:** No payments in v1.
- **AI features:** Sustainability assistant, emission insights/summaries, structured reduction plans, personalized alternatives, best-effort bill/receipt image extraction.
- **Currency:** N/A — no commerce; emissions are in **kg CO2e**; consumption uses native units.
- **Languages:** English + Arabic (RTL), always. Docs in English.
- **Database:** SQLite only.
- **Deployment:** local demo (`127.0.0.1:5000`, Android emulator `10.0.2.2:5000`).

The full spec is in `docs/`:
- `docs/00-overview.md` — personas, journeys, scope
- `docs/features/` — one page per feature
- `docs/07-roadmap.md` — milestones
- `docs/issues.md` — issue map
- `docs/ai-features.md` — AI feature contract
- `docs/diagrams/` — diagrams
- `docs/screenshots/` — screenshot library

### Open questions

| ID | Question | Default used |
|---|---|---|
| Q1 | Final app name and branding | CarbonWise / `carbonwise` |
| Q2 | Emission-factor geography | International documented defaults with editable region |
| Q3 | Organization membership model | One owner per organization in v1 |
| Q4 | Default locale | Device-follow with Arabic fallback |
| Q5 | Local notifications package | `flutter_local_notifications` + `timezone` |
| Q6 | Mobile export | CSV/share via `share_plus` + `path_provider` |
| Q7 | Admin UI language | English UI; bilingual content fields |
| Q8 | Document AI | Best-effort vision via `openrouter/free`; manual fallback |

---

## 13. Change log

| Date | Change |
|---|---|
| 2026-11-19 | Rules v1 generated from the app-bootstrap kit for CarbonWise. |
| 2026-11-19 | Added AI best-effort vision, consent, no-invented-numbers, and startup guards. |
