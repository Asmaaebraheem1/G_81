# INTAKE — CarbonWise (Phase 0)

> **Status: AWAITING OWNER REVIEW — DO NOT IMPLEMENT.**
> Only this `INTAKE.md` has been created. No rules, skills, docs, issues, repository, or code will be created until you explicitly approve this document.
>
> - Prepared: **2026-11-19**
> - Workspace: `D:\projects_is_2026\G_81`
> - Proposed GitHub repo: `Asmaaebraheem1/G_81` (private)
> - Proposed app: **CarbonWise** (`carbonwise`)
> - Fixed stack: Flutter + BLoC + Dio + sqflite / Flask + Jinja2 + SQLite / OpenRouter `openrouter/free`
> - Languages: English + Arabic (RTL) in the app; English docs
> - Payments: none in v1
> - Review mode: staged approval (details in answer 15)

---

## 1. Idea

The complete APP_IDEA supplied by the owner is reproduced **verbatim in Appendix A** at the end of this file.

### One-paragraph restatement

**CarbonWise** is an AI-assisted sustainability platform for individuals, households, and organizations. Users record consumption and activities — electricity, gas and fuel, road transport, flights, water, household/business activities, and waste — optionally upload a bill or receipt for AI-assisted data extraction and confirmation, and the backend calculates estimated emissions in **kg CO2e** from documented emission factors using transparent formulas. The app turns those calculations into dashboards, reports, goals, sustainable alternatives, challenges, achievements, and notifications. A backend-only OpenRouter integration (`openrouter/free`) powers a grounded sustainability assistant, report explanations, personalized recommendations, structured reduction plans, and best-effort image extraction. AI output is always separated from backend-calculated numbers. A professional Flask + Jinja2 Admin Dashboard manages users, organizations, emission categories and factors, records and documents, plans, goals, reports, challenges, notifications, educational content, AI usage, roles, and platform settings.

---

## 2. Phase 0 — the 15 questions and proposed answers

> You may reply **“defaults”** to accept every recommended answer below, or correct any item by number.

### 1) App name

**CarbonWise** — display name: `CarbonWise`; slug/package: `carbonwise`; Android application ID: `com.carbonwise.app`; Arabic brand: `كربونوايز`.

- Alternatives if you dislike it: **CarbonLedger**, **GreenTrace**, **EcoMeter**.
- The repository/folder remains `G_81` unless you prefer the repo to be named `carbonwise`.
- The name is a proposal only; renaming after Phase 5 is expensive (package IDs, repo, docs, seed), so please confirm now.

### 2) One-line pitch

**“CarbonWise helps individuals, households, and organizations measure their carbon footprint, understand what drives it, and follow a transparent, AI-assisted plan to reduce it.”**

### 3) Actors

| Actor | Auth | Goal |
|---|---|---|
| **Guest** | none | Browse public educational content, switch language, understand the product, register/login. Cannot record data or use personalized AI. |
| **Individual / household user** | JWT | Track personal or household consumption, view reports, set goals, use AI, join challenges. |
| **Organization user** | JWT | Same capabilities scoped to an organization profile and its records. One owner account per organization in v1. |
| **Administrator** | signed cookie session + CSRF | Operate the platform through the Jinja Admin Dashboard. Two v1 roles: `super_admin` and `content_editor`. |
| **OpenRouter** | server-side API key | External AI provider; not a human actor. Appears in the context diagram as an external system. |

### 4) Top 5 user journeys

1. **First footprint** — register → choose individual/household/organization → complete profile → add electricity, transport, and waste records → see the calculated dashboard with a formula breakdown for every record.
2. **Bill to record** — upload an electricity bill or fuel receipt image → AI extracts candidate values → user confirms or corrects them → backend validates and calculates → dashboard updates.
3. **Understand and reduce** — open a report → ask the AI assistant or generate insights → create a percentage reduction goal → generate a structured reduction plan → complete actions → track progress.
4. **Choose a better alternative** — open sustainable alternatives → filter by category/impact → save or accept an alternative → see the calculated estimated impact and optionally add it to a plan.
5. **Stay engaged** — join a challenge → record progress or complete an action → earn points/badges → receive a notification → view the opt-in leaderboard.

**Admin journey:** log in → dashboard KPIs → search/manage a user or organization → review consumption records and uploaded documents → edit an emission factor → review AI usage and a reported response → publish content/challenge/announcement → export an analytics report.

### 5) Platforms

- **Android only**, Flutter stable channel (verified locally: Flutter 3.47.9 / Dart 3.13.7).
- The Admin Dashboard is **server-rendered web** (Flask + Jinja2) served by the same backend.
- No iOS, desktop, mobile web, or separate web frontend in v1.
- Local demo only; no cloud deployment.

### 6) Admin panel scope

All sections from the idea are in v1. Jinja pages are English in v1; content fields are bilingual.

| Admin area | Required capabilities |
|---|---|
| Login / shell | Cookie session, CSRF, logout, responsive navigation |
| Dashboard overview | Users, active accounts, organizations, records, total estimated emissions, goal/plan progress, AI calls, recent activity, charts |
| User management | Search, filter, view, activate/suspend, reset password, view records/goals/plans, soft-delete |
| Organization management | Search, view, verify/suspend, view associated records and sustainability summary |
| Emission categories | Create/edit/deactivate, bilingual names, order, icon/image, unit hints |
| Emission factors | Create/edit/version, source name/URL, unit, region, valid-from/valid-to, active flag; factor snapshots on records |
| Consumption records | Search/filter, view calculation breakdown, attachments, flag/soft-delete |
| Documents | List, metadata, authenticated download, extraction status, delete |
| Reduction plans | List, view actions, status, reported issues, flag; AI generation is user-triggered, not admin-triggered |
| Sustainability goals | List, progress, status, filter by period/account |
| Reports and analytics | Aggregates by category, period, account type, organization; CSV export |
| Challenges and rewards | CRUD challenges, rules, points, badges, leaderboard settings |
| Notifications | Create announcements, target all/segment, list, delete, view delivery stats |
| AI assistant monitoring | Usage, models returned, token/cost-free budget, failures, flagged/reported responses, AI settings (model fixed to `openrouter/free`) |
| Content management | Bilingual articles/awareness content, images, publish/unpublish, ordering |
| Admin profile and settings | Profile, password, admin accounts/roles, platform settings (thresholds, AI budget, feature flags) |
| Audit log | Sensitive admin actions recorded and viewable |

### 7) Authentication and guest rules

- **Email + password** registration and login.
- Registration chooses account type: **individual**, **household**, or **organization**; organization registration requires an organization name.
- **JWT access + refresh**: access ~30 minutes, refresh ~30 days, refresh rotation and revocation on logout. Tokens only in `flutter_secure_storage`; never in logs or SQLite.
- **Guest**: public landing/educational content and language switch only. No records, goals, plans, challenges, personalized AI, or uploads without an account.
- **Admin**: signed-cookie session + CSRF (`Flask-WTF`). Admin never uses JWT; the JSON API never accepts cookies.
- **v1 exclusions**: social login, phone/OTP login, email verification, and self-service password reset (no email provider). Admin can reset a user's password; demo users are restored by `seed --reset`.
- Basic login rate limiting and generic error messages are required.

### 8) Payments

**None.** No subscriptions, ads, in-app purchases, paid AI, or payment gateway in v1. `CURRENCY` is **N/A**; emission values use **kg CO2e**, and consumption uses native units (`kWh`, `m³`, `L`, `km`, `kg`, etc.).

### 9) Languages

- **English + Arabic (RTL)** in the mobile app, always.
- No third language.
- Default locale: follow the device when it is English or Arabic; otherwise fall back to **Arabic (`ar`)**. The user can switch at any time; the preference persists.
- All app strings go through ARB files (`app_en.arb`, `app_ar.arb`); no hardcoded user-facing strings.
- Bilingual database content: `*_en` and `*_ar` for categories, factors’ display names, articles, challenges, alternatives, and badges.
- Admin UI: English in v1; admin can edit both Arabic and English content fields.
- RTL is verified on every screen, not only the home screen.

### 10) AI features and policy

**Enabled.** The app uses **OpenRouter through the backend only**, with the fixed model **`openrouter/free`** (Free Models Router). No paid model, no fallback model, no independent model training or fine-tuning.

| AI feature | Input | Output | Modality |
|---|---|---|---|
| Sustainability assistant chat | User question + server-built context from calculated data | Text answer with practical suggestions | Text |
| Emission report analysis / insights | Calculated totals, category breakdown, trend, goals, recent records | Validated structured insights + explanation | Text |
| Sustainability summaries | Period totals and comparisons | Plain-language summary | Text |
| Structured reduction plans | Goal, baseline, top categories, constraints/preferences | Validated JSON plan: actions, priority, timeline, assumptions | Text |
| Personalized alternatives | User patterns + curated alternatives catalog | Selected alternative IDs + rationale (backend validates IDs and calculates impact) | Text |
| Bill/receipt extraction | Uploaded image + minimal instructions | JSON candidate fields + confidence | Image + text, **best effort** |

**Rules:**

- The backend injects actual calculated values; the AI may explain them but **must not invent emission values**. AI never writes directly to the database.
- Structured AI outputs are validated against a schema; malformed output is rejected and retried at most once, then a friendly fallback is shown.
- **Vision is best-effort.** `openrouter/free` routes among free models; if the selected model does not support image input, the backend returns a typed `vision_unavailable` error and the app falls back to manual entry. No paid vision model is used.
- Extracted bill data is **never saved automatically**; the user must confirm/correct it, and the backend validates it before calculation.
- No prompt or response containing personal data is logged. Usage metadata (feature, model returned, token counts, latency, status) is stored. Reported AI responses may be stored after PII redaction for admin review.
- AI requests are rate-limited, budgeted, and cached; all AI calls are mocked in tests. Without an API key, AI features fail gracefully and the app offers calculated/rules-based alternatives.
- Free OpenRouter models may have different data-retention/training policies. Before sending a bill image, the app shows a clear consent notice; manual entry is always possible. This limitation must be documented in `docs/ai-features.md`.

### 11) Seed and demo data

Deterministic, idempotent, with `seed --reset`, using a fixed six-month demo window (no randomness).

| Item | Proposed seed |
|---|---|
| Admins | 1 `super_admin` + 1 `content_editor` |
| Users | 3: English-default individual, Arabic-default household, organization owner; 1 additional guest-only flow (no account) |
| Organizations | 1 demo organization |
| Emission categories | 7: Electricity, Gas & Fuel, Road Transport, Flights, Water, Household & Business, Waste |
| Emission factors | 20 documented factors with source, source URL, year, region, unit, validity, active flag |
| Consumption records | 60 across six months (30 individual, 15 household, 15 organization), mixed categories and statuses |
| Documents | 3 sample bill/receipt images with confirmed extraction results |
| Goals | 4: active weekly, active monthly, completed yearly, missed |
| Reduction plans | 3: active, completed, draft; 3–6 actions each; 2 cached AI-style demo plans clearly labeled `demo` |
| Alternatives | 12 curated alternatives with documented impact assumptions |
| Challenges | 5: active, upcoming, completed; weekly/monthly types |
| Badges / points | 12 badges + 20 points-ledger entries |
| Notifications | 8 across reminder, goal, significant-increase, plan, challenge, monthly summary, admin announcement; read/unread |
| Content | 8 bilingual educational articles with relevant images |
| AI demo rows | Cached sample assistant/insight/plan outputs labeled `demo`, plus 10 `ai_usage` metadata rows; no real key required for the demo |
| Admin audit | 10 sample audit entries |

All demo logins and reset commands will be documented in `docs/demo-script.md` and `docs/02-configuration.md`. No real secrets in seed data.

### 12) Uploads

- Accept **JPG, PNG, WebP** images and **PDF** attachments.
- Images can be used for best-effort AI extraction; PDFs are stored as attachments but **not** AI-extracted in v1 (manual entry).
- Max **10 MB per file**, **30 MB per request**.
- Store privately under `backend/instance/uploads/` (not public static), with generated filenames and authenticated download routes.
- Validate MIME type by content (not just extension), strip unsafe metadata where feasible, never execute uploaded files, and never expose directory listings.
- Admin can view metadata, download through an authenticated route, and delete. Users can delete their own unconfirmed documents.
- No cloud storage.

### 13) Deployment

**Local demo only.**

| Surface | Address |
|---|---|
| API | `http://127.0.0.1:5000/api/v1` |
| Swagger | `http://127.0.0.1:5000/api/` |
| Admin | `http://127.0.0.1:5000/admin/login` |
| Mobile (Android emulator) | `http://10.0.2.2:5000/api/v1` |
| Physical phone | Backend `HOST=0.0.0.0` + PC LAN IP |

- Windows **cmd** only in all commands, scripts, and docs.
- No Docker, cloud hosting, Redis, Firebase, or external database.
- The backend and Admin Dashboard run in one Flask process.

### 14) Repository

| Item | Proposed value |
|---|---|
| Owner | `Asmaaebraheem1` (from `gh auth status`) |
| Repo | `G_81` (matches folder name) |
| Visibility | **private** |
| Default branch | `main` |
| Source folder | `D:\projects_is_2026\G_81` |
| License | private/demo; no open-source license unless requested |

`gh auth status` currently shows the `workflow` scope, so CI files can be pushed. If you prefer the repo to be named `carbonwise`, confirm before Phase 5.

### 15) Review mode

**Staged review** — the owner is present at phase gates; the build loop still uses yoyo inside an approved issue.

- **Now:** explicit approval of this `INTAKE.md` before any other file is created.
- **Phases 1–3:** show the rules, skills, and docs index for review before implementation.
- **Phases 4–6 (per issue):** steps 4–6 (docs → code → tests) run in yoyo without mid-implementation questions; decisions are reported at review.
- **Push/merge:** only after review confirmation and green checks. No push to `main`, ever.
- You may switch to full yoyo later by saying **“go yoyo”**; until then, this staged mode applies.

---

## 3. Assumptions (marked explicitly)

| ID | Assumption | Impact if wrong |
|---|---|---|
| A1 | The name **CarbonWise** / `carbonwise` is acceptable. | Renaming touches package IDs, repo, docs, seed, screenshots. |
| A2 | One account model covers individual, household, and organization; **one owner per organization** in v1; no member invitations, staff roles, or multi-user organizations. | Multi-member organizations add membership tables, permissions, invites, and admin pages. |
| A3 | Emission factors use **documented international defaults** (e.g., EPA/DEFRA/IPCC and published grid factors) with source, year, region, and validity stored; admins can edit them. The demo does not claim a specific country’s official inventory. | A country-specific factor set (e.g., Palestine) requires a confirmed geography and sources. |
| A4 | All emission values and estimated savings are **backend-calculated** from factor snapshots and documented formulas. AI only explains, summarizes, structures, or recommends; it never supplies numeric emission values. | If AI-generated numbers were allowed, the app could not be auditable. |
| A5 | Vision extraction through `openrouter/free` is **best-effort**; the routed free model may not support image input. Manual entry is always the fallback. | A guaranteed OCR/vision feature would require a paid or separately trained model, which violates the fixed stack. |
| A6 | Notifications in v1 are **in-app + local scheduled reminders**; no Firebase/cloud push. The exact local-notification package needs approval (see §9). | Cloud push would require Firebase or another provider and is out of scope. |
| A7 | Challenge completion is **system-verified where measurable** (e.g., reduction vs baseline, record streak) and **self-reported + optional evidence + admin review** otherwise. It is not audited verification. | A stricter verification model adds review workflows and evidence storage. |
| A8 | Report export is **CSV + print-friendly HTML**; mobile can share a CSV or copy a summary if the share plugin is approved. Server-side PDF generation is out of scope unless approved. | A PDF requirement adds a backend PDF library and template work. |
| A9 | Default locale follows the device when EN/AR, otherwise Arabic; user can switch; admin UI is English in v1. | If the admin UI must be bilingual, add Jinja l10n infrastructure. |
| A10 | Admin roles in v1 are `super_admin` and `content_editor` with a simple permission matrix; granular per-action permissions are later. | Full RBAC adds tables, UI, and testing. |
| A11 | Timestamps are UTC; the user profile stores an IANA timezone for period boundaries (week/month/year). | Local-time period calculations would be ambiguous. |
| A12 | Uploads are private under `backend/instance/uploads/`, not public static. | Public static uploads would leak bills/receipts. |
| A13 | Visual assets are downloaded from free-license sources (Unsplash/Pexels) and stored locally with credits; no hotlinking. | Licensing/source constraints may require alternative assets. |
| A14 | No email, SMS, payment, or cloud-push provider is integrated in v1. | Each adds an external dependency and secrets. |
| A15 | CarbonWise is an **estimator**, not a certified carbon audit or regulatory reporting tool. Disclaimers appear in the app and docs. | A compliance claim would require audited methodologies and legal review. |
| A16 | Screenshots are produced from a deterministic demo/screenshot mode; diagrams are black-and-white PNG exports with editable sources. Tooling is chosen in Phase 3. | A fully automated screenshot pipeline may need dev-only tools. |
| A17 | Additional packages listed in §9 are approved unless the owner says otherwise. | Without them, charts, uploads, reminders, and export are reduced or custom-built. |
| A18 | Organization records belong to a single organization profile; no facility/site hierarchy in v1. | Multi-site organizations add a `facilities` table and scoping. |
| A19 | AI budget defaults: **200,000 tokens/day** global and **20 requests/hour/user**, with prompt-hash cache scoped per user/context. | Different limits may be set by config. |
| A20 | The app uses a clean Material 3 design with a sustainability palette and bundled fonts/assets; the admin uses custom CSS, no CDN. | A different design system may add dependencies. |

---

## 4. Out of scope for v1

- iOS, desktop, mobile web, and a separate SPA frontend.
- Payments, subscriptions, ads, in-app purchases, or paid AI tiers.
- Social/phone login, email verification, and self-service password reset.
- Cloud deployment, Docker, Redis, PostgreSQL/MySQL/MongoDB, Firebase/Firestore, Supabase, Hive/Isar/Drift/ObjectBox/Realm.
- Multi-user organizations, invitations, SSO, facility/site hierarchies.
- Smart-meter, utility, bank, or supplier integrations; IoT ingestion.
- Carbon-offset marketplace, credit purchasing, or trading.
- Custom ML model training/fine-tuning; any AI provider other than OpenRouter; any model other than `openrouter/free`.
- Guaranteed OCR for arbitrary documents; automated PDF table extraction; handwritten-document guarantees.
- Audited/certified carbon accounting, regulatory reporting (GHG Protocol/CSRD/ISO claims), tax, or legal advice.
- Full offline CRUD sync and conflict resolution; offline read cache only.
- Cloud push notifications (FCM/APNs) and email/SMS notifications.
- Advanced BI/warehouse analytics; v1 uses SQLite aggregates and CSV export.
- Third-party public API, webhooks, or marketplace.
- Server-side PDF generation unless separately approved.
- User-generated public content beyond challenge participation and opt-in leaderboard aliases.
- More than English + Arabic.

---

## 5. Proposed v1 feature list (15 features)

| ID | Feature | One-line scope | Primary area |
|---|---|---|---|
| **F01** | Accounts, profiles & preferences | Register/login/refresh/logout; individual, household, organization profiles; EN/AR preference; guest read-only mode | API + app + admin |
| **F02** | Emission categories & documented factors | Bilingual category catalog and versioned emission factors with source, unit, region, validity, and factor snapshots | API + admin |
| **F03** | Consumption records & calculation engine | Manual entry for all activity types; transparent backend `quantity × factor` calculations; formula breakdown | API + app |
| **F04** | Bill & document uploads with AI extraction | Private image/PDF upload; best-effort AI extraction; mandatory user confirmation; attachment linkage | API + app + AI |
| **F05** | Carbon dashboard, reports & export | Totals, category breakdown, trends, comparisons, top activities, progress, CSV/print-friendly export | API + app |
| **F06** | Sustainability goals | Weekly/monthly/yearly percentage-reduction goals with stored baseline, deadlines, progress, and status | API + app |
| **F07** | AI sustainability assistant | Grounded chat over the user’s calculated data; suggested prompts; conversation history; graceful failure | API + app + AI |
| **F08** | AI emission insights & summaries | Top sources, unusual changes, category comparisons, reduction opportunities, period summaries; server-injected values only | API + app + AI |
| **F09** | AI reduction plans | Structured actions, priorities, timeline, assumptions; backend-calculated estimated savings; action tracking | API + app + AI |
| **F10** | Sustainable alternatives & recommendations | Curated alternatives catalog + AI personalization; estimated impact; save/accept/add-to-plan | API + app + AI |
| **F11** | Challenges, achievements & leaderboard | Challenges, progress, points ledger, badges, milestones, opt-in leaderboard | API + app + admin |
| **F12** | Notifications & reminders | In-app notification center, unread counts, preferences, goal/plan/challenge reminders, significant-increase alerts, summaries | API + app + admin |
| **F13** | Admin core, users & organizations | Cookie login, dashboard KPIs, user/organization search and control, admin roles/settings, audit log | Admin |
| **F14** | Admin catalog, records & documents | Manage categories, factors, consumption records, attachments/extractions; view calculation breakdowns; CSV export | Admin |
| **F15** | Admin programs, content, analytics & AI monitoring | Manage plans, goals, reports/analytics, challenges/rewards, notifications, bilingual content, AI usage/flagged responses, platform settings | Admin |

---

## 6. Traceability to the APP_IDEA

| APP_IDEA section | Covered by |
|---|---|
| 1. AI sustainability assistant | F07, F08 |
| 2. Carbon footprint tracking and analysis | F02, F03, F04 |
| 3. AI-powered emission data analysis | F08 |
| 4. Smart document and bill analysis | F04 |
| 5. AI-powered sustainable reduction plans | F09 |
| 6. Personalized sustainability goals | F06 |
| 7. Emission reports and data visualization | F05 |
| 8. Sustainable recommendations and alternatives | F10 |
| 9. Sustainability challenges and gamification | F11 |
| 10. Notifications and reminders | F12 |
| 11. User profiles and account management | F01 |
| 12. Comprehensive Admin Dashboard | F13, F14, F15 |
| 13. AI integration and technical approach | F02, F04, F07–F10; ADR for AI policy |
| 14. Sustainable Development Contribution (SDG 7, 11, 12, 13) | Educational content (F15), onboarding/reports copy (F05), docs |
| 15. Expected outcomes | All features; measured in demo script and acceptance criteria |
| A. System analysis diagrams | Deliverable D1 |
| B. Complete UI screenshots | Deliverable D2 |
| C. Professional visual assets | Deliverable D3 |
| D. AI features documentation | Deliverable D4 |
| E. Organization and approval | D5 + this Phase 0 gate |

---

## 7. Mandatory design and documentation deliverables

These are part of “done” for the project, not optional extras.

### D1 — System analysis diagrams

- 1. Context Diagram.
- 2. Data Flow Diagram (DFD) — Level 0.
- 3. Data Flow Diagram (DFD) — Level 1.
- 4. Use Case Diagram.
- 5. Entity Relationship Diagram (ERD).
- **Strictly black and white**; no colors, gradients, shadows, or decorative effects.
- Clear, professional, properly structured, and readable.
- Export **each diagram as a separate high-quality PNG** (target 300 DPI) plus an editable source file.
- Folder: `docs/diagrams/` with a `README.md` index and consistent names:
  `01-context.png`, `02-dfd-level-0.png`, `03-dfd-level-1.png`, `04-use-case.png`, `05-erd.png`.
- Proposed tooling: PlantUML (Java 21 is available) or a Python/Pillow renderer; final choice and any dev-only tool recorded in Phase 3. No runtime dependency.

### D2 — Complete UI screenshot library

- Folder: `docs/screenshots/` with `mobile/` and `admin/` subfolders, plus `README.md` containing a coverage matrix.
- Covers **every screen and every important UI state**:
  - main screens/navigation, registration/login, profile/settings, consumption entry, document upload, dashboard, category details, AI assistant, plans, goals, reports, alternatives, challenges/rewards/achievements, notifications;
  - admin overview, all admin management pages, forms, tables, detail pages;
  - empty, loading, success, error, confirmation, validation, search/filter, disabled/permission states.
- Mobile screenshots in **English and Arabic (RTL)** for every screen; admin screenshots in English (admin UI language v1).
- Naming convention: `<area>-<screen>-<state>-<locale>.png`, e.g. `mobile-dashboard-success-en.png`, `admin-users-empty-en.png`.
- Generated from a deterministic screenshot/demo mode with seeded data; no real personal data.
- Proposed approach: Flutter emulator/integration captures + headless Edge/browser captures for admin; exact tooling finalized in Phase 3. The requirement is the complete set, not a few representative images.

### D3 — Professional visual assets

- Relevant images for: climate/carbon, renewable energy, sustainable transport, energy efficiency, environmental protection, sustainable lifestyles, resource conservation, waste/recycling, water.
- Store locally, optimized, with a documented source and license:
  - app: `mobile/assets/images/`
  - admin/content: `backend/app/static/assets/images/`
  - credits/index: `docs/assets/credits.md` and `docs/assets/README.md`
- No irrelevant stock images, low-quality visuals, hotlinked URLs, or generic gray placeholders.
- Use images in onboarding, empty states, category headers, educational content, challenge cards, and admin content previews.

### D4 — AI features documentation

A dedicated documentation set covering every AI feature:

- Purpose and functionality.
- User input and server-injected context.
- Expected output and validation schema.
- OpenRouter integration and the fixed `openrouter/free` model.
- Supported input types: text; image only when the routed free model supports vision.
- Backend/mobile integration and data flow.
- Limitations, consent, privacy, retries, rate limits, budgets, and fallbacks.
- Clear separation between **AI-generated recommendations** and **backend-calculated values**.
- No independent model training; no paid fallback.
- Planned pages: `docs/ai-features.md`, `docs/backend/ai-integration.md`, and an ADR (`docs/decisions/ADR-0002-ai-model-policy.md`).

### D5 — Organization and approval

- All documentation, diagrams, screenshots, and visual assets live in clearly named folders with index files.
- `docs/README.md` links every page.
- This `INTAKE.md` is the Phase 0 approval gate.
- No repository, rules, skills, docs, issues, or code are created until the owner approves this document.
- After approval, Phases 1–3 are reviewed at their gates before implementation.

---

## 8. Proposed milestone order

| Milestone | Scope | Why this order |
|---|---|---|
| **M0 — Foundation** | Backend scaffold, mobile scaffold, schema/migrations/seed, CI, health endpoint | Everything depends on a running, tested skeleton |
| **M1 — Identity** | F01 accounts/profiles/guest rules | Ownership and permissions must exist before domain data |
| **M2 — Data & calculation** | F02 categories/factors, F03 records/calculation engine | No reports or AI without real calculated data |
| **M3 — Evidence** | F04 uploads + AI extraction | Depends on records and factors |
| **M4 — Insight** | F05 dashboard/reports, F06 goals | Needs M2/M3 data |
| **M5 — AI** | F07 assistant, F08 insights, F09 plans, F10 alternatives | AI needs the domain data and calculations first |
| **M6 — Engagement** | F11 challenges/rewards, F12 notifications | Depends on records, goals, plans, and AI data |
| **M7 — Admin** | F13 core/users/orgs, F14 catalog/records, F15 programs/content/AI | Admin management follows the domain it manages |
| **M8 — Design & docs** | D1 diagrams, D2 screenshots, D3 assets, D4 AI docs | ERD/DFD early; complete screenshot set at UI freeze |
| **M9 — Hardening** | Coverage ≥ 50%, EN/AR/RTL audit, smoke test, demo script, docs sync, final review | Prove it works and hand over |

The normal build loop is one issue → one branch → one PR, with docs/code/tests in yoyo inside each approved issue.

---

## 9. Packages/tooling that need your approval

The fixed stack already covers Flutter + BLoC + Dio + sqflite + freezed + go_router + flutter_secure_storage and Flask + Jinja + SQLAlchemy + Flask-Migrate + flask-openapi3 + pydantic + Flask-JWT-Extended + Flask-WTF + httpx. The following additional packages are proposed for the capabilities the idea requires. If you prefer, we can reduce scope instead of adding them.

### Backend (runtime)

| Package | Why | If not approved |
|---|---|---|
| `Pillow` | Validate image content, create safe thumbnails, strip unsafe metadata | Basic header checks only; weaker image validation |
| `email-validator` | Pydantic `EmailStr` validation | Regex email validation only |

### Mobile (runtime)

| Package | Why | If not approved |
|---|---|---|
| `fl_chart` | Interactive line/bar/pie charts for reports and dashboard | Custom painters; more time, less interactive |
| `image_picker` | Camera/gallery capture for bills and receipts | File picker only; no camera capture |
| `file_picker` | PDF attachment selection | Images only; no PDF attachments |
| `flutter_local_notifications` + `timezone` | Scheduled local reminders on Android | In-app notification center only |
| `share_plus` + `path_provider` | Export/share a CSV or summary from the app | View-only summary + copy text; admin can still export |
| `intl` | Required for EN/AR dates/numbers | Not possible; already required by l10n |

### Development / tooling (not runtime)

| Tool | Why | If not approved |
|---|---|---|
| `pytest`, `pytest-cov`, `ruff`, `black` | Already in the runbook | Required; not optional |
| `mocktail`, `bloc_test`, `build_runner`, `freezed`, `json_serializable` | Flutter tests/codegen | Required by the fixed stack conventions |
| PlantUML jar **or** a Python/Pillow renderer | Black-and-white diagram exports | Manual drawing; harder to keep consistent |
| Headless Edge (already installed) or a dev-only Playwright/Selenium script | Automated admin screenshots | Manual browser captures; slower and less repeatable |
| Android SDK emulator + `adb` | Mobile screenshots and smoke testing | Manual device screenshots |

No paid AI model, no Firebase, no cloud database, and no alternative state-management library are proposed.

---

## 10. Decisions that materially change scope — please confirm

These are the points where a small answer changes the plan. Everything else can be answered “defaults”.

1. **App name:** `CarbonWise` / `carbonwise` — confirm or choose an alternative.
2. **Emission-factor geography:** use documented international defaults (recommended) or a specific country’s official factors? If a country, which one?
3. **Organization model:** one owner per organization in v1 (recommended) or multi-member organizations?
4. **Default locale:** device-follow with Arabic fallback (recommended), English fallback, or fixed Arabic/English?
5. **Local reminders:** approve `flutter_local_notifications` + `timezone` (recommended) or in-app notifications only?
6. **Mobile export:** approve `share_plus` + `path_provider` (recommended) or view-only summary?
7. **Admin UI language:** English-only admin UI with bilingual content fields (recommended) or fully bilingual admin UI?
8. **Document AI:** accept best-effort vision via `openrouter/free` with manual fallback (required by the stack), or remove AI extraction and keep uploads as attachments only?
9. **Roles:** `super_admin` + `content_editor` in v1 (recommended) or a deeper RBAC matrix now?
10. **Screenshots:** approve the deterministic screenshot mode + headless browser approach (recommended) or produce screenshots manually?

---

## 11. Phase 0 sanity checklist

| Check | Status |
|---|---|
| Idea restated and owner agrees | ⬜ pending your approval |
| At least 5 end-to-end user journeys | ✅ J1–J5 + admin journey |
| Every actor has at least one journey | ✅ guest, user, organization user, admin |
| Admin scope explicit | ✅ 17 page groups in §2.6 |
| Auth + guest rules explicit | ✅ §2.7 |
| Payment choice explicit | ✅ none |
| AI choice explicit | ✅ `openrouter/free`, backend-only, best-effort vision |
| Seed data enough to demo without manual setup | ✅ §2.11 |
| Languages = EN + AR (RTL) | ✅ §2.9 |
| Repo name/owner confirmed | ⬜ proposed `Asmaaebraheem1/G_81`, private |
| Review mode confirmed | ⬜ proposed staged review |
| Mandatory diagrams/screenshots/assets/AI docs planned | ✅ D1–D4 |
| No implementation started | ✅ only this `INTAKE.md` exists |

**Phase 0 is complete only when you approve this document.** Please reply with either:

- **“INTAKE approved — defaults”** (accept all recommended answers and the proposed packages), or
- a numbered list of corrections, or
- **“INTAKE approved with changes: …”**

After explicit approval, I will proceed to **Phase 1 — generate `agent.md`, `AGENTS.md`, and `.gitignore`**, and stop at the next review gate.

---

## Appendix A — APP_IDEA (verbatim, as supplied)

# AI-Powered Emissions Analysis and Sustainable Reduction Planning Application

Develop a comprehensive AI-powered mobile application supported by a professional web-based Admin Dashboard to help individuals, households, and businesses understand, monitor, and reduce their carbon emissions through intelligent analysis, personalized sustainability recommendations, and practical emission-reduction plans.

The platform will provide users with a centralized environment to record their daily activities, track energy and resource consumption, estimate their carbon footprint, identify the main sources of emissions, and receive customized plans to reduce their environmental impact.

The application will use **OpenRouter API as its primary AI integration**, providing access to suitable language and multimodal AI models through a unified API without requiring the development and training of multiple independent AI models.

### 1. AI-Powered Sustainability Assistant

Integrate an intelligent chatbot that acts as a personal sustainability advisor. Users can ask questions about carbon emissions, climate change, energy efficiency, sustainable practices, and ways to reduce their environmental impact.

The assistant should provide understandable explanations, practical suggestions, and recommendations based on the user's recorded consumption data and sustainability goals.

It should also help users understand their emission reports and explain the meaning of different environmental indicators.

### 2. Carbon Footprint Tracking and Analysis

Allow users to record and monitor activities that contribute to their carbon footprint, including:

- Electricity consumption.
- Gas and fuel consumption.
- Transportation and commuting.
- Flights and travel activities.
- Water consumption.
- Household and business activities.
- Waste generation and disposal.

Users should be able to enter information manually or upload supporting documents, such as electricity bills or fuel consumption records, when applicable.

The system will organize the collected information into categories and calculate estimated emissions using documented emission factors and predefined calculation formulas.

### 3. AI-Powered Emission Data Analysis

Use OpenRouter to analyze the user's recorded consumption information and generated emission reports.

The AI will help users:

- Identify the activities contributing most to their emissions.
- Explain unusual changes in their carbon footprint.
- Compare emission categories.
- Highlight areas with significant reduction opportunities.
- Provide understandable insights based on historical consumption data.

The AI should use actual calculated results provided by the backend rather than inventing emission values.

### 4. Smart Document and Bill Analysis

Allow users to upload electricity bills, fuel receipts, and other relevant consumption documents.

When the selected OpenRouter model supports image input, the application can use its multimodal capabilities to extract and interpret visible information from uploaded documents.

The system should identify relevant information such as consumption values, billing periods, and usage details, then ask users to confirm extracted information before saving it.

The backend will use the confirmed data in its emission calculations.

### 5. AI-Powered Sustainable Reduction Plans

One of the main features of the application is generating personalized emission-reduction plans.

Based on the user's consumption history, carbon footprint reports, and selected environmental goals, OpenRouter-powered AI will generate practical recommendations and structured action plans.

Examples include:

- Reducing unnecessary electricity consumption.
- Improving household energy efficiency.
- Choosing more sustainable transportation options.
- Reducing fuel consumption.
- Improving waste management practices.
- Reducing water and resource consumption.
- Adopting more sustainable daily habits.

Each plan should include recommended actions, expected benefits, suggested priorities, and a practical timeline.

The system should distinguish between calculated emission reductions and AI-generated recommendations. Estimated savings must be based on documented assumptions and calculation methods.

### 6. Personalized Sustainability Goals

Allow users to create personal environmental goals, such as reducing their carbon footprint by a specific percentage within a selected period.

Users can define weekly, monthly, or yearly goals and track their progress through dedicated dashboards.

The application will monitor progress based on recorded activities and calculated emission values, showing whether users are moving toward their selected targets.

### 7. Emission Reports and Data Visualization

Provide detailed reports and interactive visualizations to help users understand their environmental impact.

The reporting section should include:

- Total estimated carbon emissions.
- Emissions by category.
- Monthly and yearly emission comparisons.
- Historical consumption trends.
- Highest-emission activities.
- Progress toward reduction targets.
- Estimated reductions achieved.
- Comparison between previous and current periods.

Users should be able to view detailed reports and export their sustainability summaries when needed.

### 8. Sustainable Recommendations and Alternatives

Create a dedicated section that presents practical alternatives to high-emission activities.

For example:

- Suggesting public transportation or carpooling instead of individual car use.
- Recommending energy-efficient appliances.
- Suggesting ways to reduce electricity usage.
- Encouraging reusable products and responsible consumption.
- Recommending waste reduction and recycling practices.

OpenRouter-powered AI can personalize these recommendations according to the user's consumption patterns, preferences, and reduction goals.

### 9. Sustainability Challenges and Gamification

Encourage users to adopt environmentally responsible habits through challenges, achievements, and rewards.

The application can include:

- Weekly and monthly sustainability challenges.
- Personal environmental milestones.
- Achievement badges.
- Points for completing verified sustainable actions.
- Progress tracking.
- Leaderboards.
- Community challenges.

Examples of challenges include reducing electricity consumption, using public transportation, and reducing household waste.

### 10. Notifications and Reminders

Provide notifications to help users maintain sustainable habits and stay engaged with their environmental goals.

Notifications may include:

- Reminders to record consumption data.
- Updates about sustainability goals.
- Alerts when emissions increase significantly.
- Notifications about incomplete reduction-plan activities.
- Challenge reminders.
- Monthly and yearly environmental summaries.

### 11. User Profiles and Account Management

Provide a complete user account system with registration, login, and profile management.

Each user profile should include:

- Personal information.
- Household or organization information, depending on account type.
- Consumption history.
- Carbon footprint reports.
- Reduction plans.
- Sustainability goals.
- Completed challenges.
- Achievements and points.
- Notification preferences.

### 12. Comprehensive Admin Dashboard

Develop a professional web-based Admin Dashboard that provides centralized management and monitoring of the platform.

The dashboard should contain multiple organized sections:

- **Dashboard Overview:** Display platform statistics, registered users, active accounts, total recorded emissions, reduction progress, and recent activities.
- **User Management:** Search, view, manage, and control user accounts.
- **Organization Management:** Manage business or organization profiles and their associated sustainability records.
- **Emission Categories Management:** Manage emission categories, calculation settings, and relevant environmental factors.
- **Emission Factors Management:** Manage documented emission factors, their sources, units, and applicable calculation periods.
- **Consumption Records Management:** Monitor recorded consumption data and submitted documents.
- **Reduction Plans Management:** Monitor generated plans and review reported plan-related issues.
- **Sustainability Goals Management:** Monitor user goals and overall progress.
- **Reports and Analytics:** View aggregated statistics and generate platform reports.
- **Challenges and Rewards Management:** Create challenges, configure points, and manage achievement rules.
- **Notifications Management:** Create announcements and manage platform notifications.
- **AI Assistant Monitoring:** Monitor AI usage, review reported responses, and manage relevant AI settings.
- **Content Management:** Manage sustainability educational content, articles, and awareness materials.
- **Admin Profile and Settings:** Manage administrator information, roles, permissions, and platform configurations.

### 13. AI Integration and Technical Approach

The application should primarily use **OpenRouter API** for its intelligent features, selecting suitable models based on their supported capabilities.

The AI integration should support:

- Natural-language conversations through the Sustainability Assistant.
- Analysis and explanation of users' emission reports.
- Identification of major emission sources from calculated data.
- Personalized sustainable recommendations.
- Generation of structured emission-reduction plans.
- Analysis of uploaded bills and consumption documents when a vision-capable model is selected.
- Generation of understandable sustainability summaries and reports.

The project should avoid unnecessary independent AI model training.

Core calculations, including carbon footprint estimation, emission comparisons, percentage reductions, and progress tracking, should be handled through backend logic using documented emission factors and transparent formulas.

OpenRouter should be integrated securely through the backend, with API keys protected on the server side. The selected AI models and their supported input types must be documented.

### 14. Sustainable Development Contribution

The project supports several United Nations Sustainable Development Goals (SDGs), particularly:

- **SDG 7 – Affordable and Clean Energy:** Encouraging efficient energy consumption and responsible energy practices.
- **SDG 11 – Sustainable Cities and Communities:** Supporting more sustainable transportation and consumption patterns.
- **SDG 12 – Responsible Consumption and Production:** Promoting efficient resource use and reducing unnecessary consumption.
- **SDG 13 – Climate Action:** Helping users understand and reduce their estimated carbon emissions.

### 15. Expected Outcomes

The expected outcome is a comprehensive digital sustainability platform that enables individuals and organizations to understand their environmental impact, identify major emission sources, and follow practical plans to reduce their carbon footprint.

By combining carbon footprint tracking, document analysis, personalized AI recommendations, sustainability goals, detailed reports, and an interactive Admin Dashboard, the application will transform emission data into understandable insights and actionable sustainability plans.

---

# FINAL DOCUMENTATION AND DESIGN REQUIREMENTS

These requirements are mandatory and must be considered during the project planning and documentation phases.

### A. System Analysis Diagrams

Create the following diagrams:

1. Context Diagram.
2. Data Flow Diagram (DFD) – Level 0.
3. Data Flow Diagram (DFD) – Level 1.
4. Use Case Diagram.
5. Entity Relationship Diagram (ERD).

**Diagram design requirements:**
- All diagrams must be strictly black and white.
- Do not use colors or decorative visual effects.
- Diagrams must be clear, professional, properly structured, and easy to read.
- Export every diagram as a separate high-quality image file.
- Keep diagram naming and organization consistent.

### B. Complete UI Screenshots

Create a separate, well-organized folder containing screenshots of **all application interfaces**, including both the mobile application and the Admin Dashboard.

The screenshots must cover every screen and every important UI state, including:

- Main screens and navigation.
- Registration and login.
- User profile and account settings.
- Consumption data entry.
- Document and bill upload.
- Carbon footprint dashboard.
- Emission category details.
- AI sustainability assistant.
- AI-generated reduction plans.
- Sustainability goals.
- Reports and analytics.
- Sustainable recommendations.
- Challenges, rewards, and achievements.
- Notifications.
- Admin dashboard overview.
- All admin management pages.
- Empty states.
- Loading states.
- Success states.
- Error states.
- Confirmation dialogs.
- Forms and validation messages.
- Search and filtering results.
- All other relevant screens and interaction states.

Do not provide only a few representative screenshots. The folder must contain a complete visual reference for the entire planned interface.

### C. Professional Visual Assets

Use high-quality, relevant external images and visual assets throughout the application wherever appropriate.

Visual assets should relate to:

- Carbon emissions and climate change.
- Renewable energy.
- Sustainable transportation.
- Energy efficiency.
- Environmental protection.
- Sustainable lifestyles.
- Resource conservation.

Avoid irrelevant stock images, low-quality visuals, and generic placeholder graphics.

### D. AI Features Documentation

Clearly document every AI feature, including:

- Its purpose and functionality.
- The user input it receives.
- The expected output.
- The OpenRouter integration and selected model.
- Whether the selected model supports text, image, or multimodal input.
- How the feature integrates with the backend and mobile application.
- Any limitations or validation requirements.

Clearly separate AI-generated recommendations from backend calculations. Emission values and estimated reductions must use documented calculation methods and reliable emission factors.

Do not introduce unnecessary independently trained AI models unless they are genuinely required and explicitly justified.

### E. Organization and Approval

Keep all documentation, diagrams, screenshots, and visual assets organized in clearly named folders.

**Important:** Begin with Phase 0 only. Create `INTAKE.md` for review and do not create additional project files or proceed to implementation until I have reviewed and explicitly approved the intake document.
