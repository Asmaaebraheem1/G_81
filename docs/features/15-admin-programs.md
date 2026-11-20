# 15 — Admin programs, content, analytics & AI

## Purpose

Let admins monitor and manage plans, goals, reports, challenges/rewards, notifications, bilingual
content, AI usage/flagged responses, and platform settings.

## UI (Jinja2)

| Page | Elements |
|---|---|
| `/admin/plans` | list, status, goal, user, action progress, detail |
| `/admin/plans/{id}` | actions, assumptions, savings, reported issues |
| `/admin/goals` | list, progress, status, period filter |
| `/admin/reports` | date/account filters, aggregates, category chart, CSV export |
| `/admin/challenges` | CRUD, rules, points, badge, dates, active |
| `/admin/badges` | CRUD, criteria, points |
| `/admin/notifications` | create announcement, target all/segment, list, delete |
| `/admin/ai` | usage, models, tokens, status mix, failures, flagged responses, budget |
| `/admin/content` | article CRUD, EN/AR, image, publish/unpublish, order |
| `/admin/settings` | AI budget, thresholds, feature flags (super admin) |

States: empty, loading skeleton, success, validation error, confirmation, no permission, filter no
results, AI disabled.

## Screen logic

- Server-side filters/pagination.
- Plans/goals: read + flag/reported-issue review; no admin-generated AI content.
- Reports: aggregates + CSV; no personal data in CSV beyond admin scope.
- Challenges/badges: create/edit/activate; points integer; dates valid.
- Notifications: target all or a segment (account type/active); preview EN/AR; send creates rows.
- AI: metadata only; flagged responses show redacted text, notes, resolve.
- Content: bilingual fields; publish sets `published_at`; images from committed assets.
- Settings: budget/threshold validation; audit.

## Backend logic

| Route | Methods | Purpose |
|---|---|---|
| `/admin/plans` | GET | list |
| `/admin/plans/{id}` | GET/POST | detail/status/flag |
| `/admin/goals` | GET | list |
| `/admin/reports` | GET | aggregates |
| `/admin/reports/export.csv` | GET | CSV |
| `/admin/challenges` | GET/POST | list/create |
| `/admin/challenges/{id}` | GET/POST | edit/activate |
| `/admin/badges` | GET/POST | list/create |
| `/admin/badges/{id}` | GET/POST | edit |
| `/admin/notifications` | GET/POST | list/create announcement |
| `/admin/ai` | GET | usage/flagged |
| `/admin/ai/flags/{id}` | POST | resolve |
| `/admin/content` | GET/POST | list/create |
| `/admin/content/{id}` | GET/POST | edit/publish |
| `/admin/settings` | GET/POST | platform settings |

Rules:
- Content editor can manage content/challenges only; other pages read-only.
- AI settings: model read-only `openrouter/free`; budget/threshold editable by super admin.
- No raw prompts in AI monitoring; flagged responses redacted.
- Announcement targeting creates user-scoped notifications; respects preferences except
  announcements.
- Audit sensitive changes.
- CSV export respects filters; no secrets.

## Data

Tables: `reduction_plans`, `plan_actions`, `goals`, `challenges`, `badges`, `notifications`,
`articles`, `ai_usage`, `ai_flagged_responses`, `app_settings`, `admin_audit_logs`.

## Acceptance criteria

1. Admin can list plans/goals and view progress/assumptions.
2. Reports aggregate by filters and export CSV.
3. Challenge/badge CRUD validates points/dates/rules.
4. Announcements target correctly and appear in the app.
5. AI monitoring shows usage/failures/flagged responses without raw prompts.
6. Flagged response resolution persists and is audited.
7. Content CRUD/publish works with EN/AR fields and images.
8. Settings validate and persist; model remains `openrouter/free`.
9. Content editor permissions are enforced.
10. Empty/error/confirmation states render cleanly.

## Tests

| Type | File | Covers |
|---|---|---|
| Service | `tests/modules/content/test_services.py` | CRUD/publish/bilingual |
| Admin | `tests/admin/test_programs.py` | plans/goals/reports |
| Admin | `tests/admin/test_challenges.py` | CRUD/points/badges |
| Admin | `tests/admin/test_notifications.py` | targeting/list |
| Admin | `tests/admin/test_ai_monitor.py` | usage/flags/no prompts |
| Admin | `tests/admin/test_content.py` | CRUD/publish/permissions |

## Status

🟡 in progress — issue #17.

Related: #17
