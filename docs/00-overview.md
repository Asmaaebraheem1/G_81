# 00 — Overview

## What it is

CarbonWise is an AI-assisted sustainability platform for individuals, households, and
organizations. Users record consumption and activities, the backend calculates estimated
emissions from documented factors, and the app turns the results into dashboards, reports,
goals, reduction plans, alternatives, challenges, and notifications. A Flask/Jinja2 Admin
Dashboard manages the platform.

## Why it exists

Most people cannot tell which daily activities drive their emissions, and generic advice is
hard to act on. CarbonWise makes the calculation transparent, then uses AI to explain the
numbers and structure a practical reduction plan — without letting the AI invent emission
values.

## Actors

| Actor | Goal | Auth |
|---|---|---|
| Guest | Browse public educational content, switch language, understand the product, register/login | none |
| Individual / household user | Track consumption, understand reports, set goals, use AI, join challenges | JWT |
| Organization user | Same capabilities scoped to an organization profile and its records | JWT |
| Administrator | Operate the platform through the Jinja Admin Dashboard | signed-cookie session + CSRF |
| OpenRouter | External AI provider (not a human actor) | server-side API key |

Admin roles in v1: `super_admin` (all pages) and `content_editor` (content + challenges, read-only elsewhere).

## Main journeys (v1)

1. **First footprint** — register → choose individual/household/organization → complete profile →
   add electricity, transport, and waste records → see the dashboard and formula breakdown.
2. **Bill to record** — upload a bill/receipt image → AI extracts candidate values → user confirms
   or corrects → backend validates and calculates → dashboard updates.
3. **Understand and reduce** — open a report → ask the AI assistant or generate insights → create
   a percentage goal → generate a structured plan → complete actions → track progress.
4. **Choose a better alternative** — browse alternatives → filter by category/impact → save or
   accept an alternative → see the calculated estimated impact → optionally add to a plan.
5. **Stay engaged** — join a challenge → record progress or complete an activity → earn points and
   badges → receive a notification → view the opt-in leaderboard.
6. **Admin operations** — log in → dashboard KPIs → manage users/organizations → review records
   and documents → edit a factor → review AI usage/flagged responses → publish content or a
   challenge → export analytics.

## Screens (app)

| Screen | Journey | Key elements |
|---|---|---|
| Welcome / guest | Guest | Intro, language switch, login/register, educational preview |
| Login / register | J1 | Email/password, account type, validation, errors |
| Home dashboard | J1, J3 | Period selector, total kg CO2e, category chart, recent records, goal progress |
| Records list | J1 | Search/filter, category chips, empty/loading/error |
| Add/edit record | J1 | Category → factor → quantity/unit → date → notes; live estimate preview |
| Record detail | J1 | Quantity, factor, source, formula, emissions, attachment |
| Upload document | J2 | Camera/gallery/file picker, consent, upload progress, error |
| Extraction confirmation | J2 | Editable extracted fields, confidence, confirm/cancel |
| Reports | J3 | Period comparisons, trends, category breakdown, top activities, export |
| Category detail | J3 | Category trend, records, factor used, tips |
| Goals | J3 | List, create/edit, progress, status |
| Goal detail | J3 | Baseline, target, progress chart, linked plan |
| AI assistant | J3 | Chat, suggested prompts, grounded context badge, report response |
| AI insights | J3 | Top sources, anomalies, opportunities, generate/refresh |
| Reduction plans | J3 | List, generate, plan detail, actions, progress |
| Alternatives | J4 | Catalog, filters, estimated impact, save/accept |
| Challenges | J5 | List, detail, join, progress, verification |
| Achievements | J5 | Badges, points, milestones |
| Leaderboard | J5 | Opt-in, period filter, aliases |
| Notifications | J5 | Inbox, unread, preferences |
| Profile / settings | J1 | Personal, household/org, locale, timezone, leaderboard opt-in, logout |
| Organization profile | J1 | Organization details, records summary |
| Educational content | Guest/J3 | Articles list/detail, images |
| Empty/loading/error states | all | Every list and form has explicit states |

## Admin pages (Jinja)

| Page | Purpose |
|---|---|
| `/admin/login` | cookie-session login |
| `/admin/` | dashboard KPIs and recent activity |
| `/admin/users` | search, view, activate/suspend, reset password, view records |
| `/admin/organizations` | search, view, verify/suspend, sustainability summary |
| `/admin/categories` | category CRUD, bilingual names, ordering |
| `/admin/factors` | factor CRUD, source/unit/region/validity, active flag |
| `/admin/records` | record search, calculation breakdown, attachments, soft delete |
| `/admin/documents` | metadata, authenticated download, extraction status, delete |
| `/admin/plans` | plan list/detail, actions, reported issues |
| `/admin/goals` | goal list/progress |
| `/admin/reports` | aggregates, filters, CSV export |
| `/admin/challenges` | challenge CRUD, rules, points, badges |
| `/admin/badges` | badge CRUD and award rules |
| `/admin/notifications` | announcements, targeting, list |
| `/admin/ai` | AI usage, failures, flagged responses, settings |
| `/admin/content` | bilingual articles, images, publish/unpublish |
| `/admin/settings` | admin profile, roles, platform settings, thresholds |
| `/admin/audit` | sensitive admin actions |

## Scope

### v1 (demoable end-to-end)
- F01–F15 from `docs/features/README.md`.
- 5 user journeys + admin journey.
- Full EN + AR/RTL.
- Deterministic seed and local demo.
- Five black-and-white diagrams, complete screenshot library, visual assets, AI docs.

### Later
- Multi-member organizations, invitations, SSO.
- Cloud deployment, cloud push, email/SMS.
- Smart-meter/utility integrations.
- Certifications/regulatory reporting.
- More languages.

### Out of scope
- Payments, subscriptions, ads, paid AI.
- iOS, desktop, mobile web.
- Independent model training/fine-tuning.
- Guaranteed OCR for arbitrary documents.
- Carbon-offset marketplace or trading.

## Languages

English + Arabic (RTL). Every app string is an ARB key. User-facing database content is bilingual
(`*_en`, `*_ar`). The admin UI is English in v1; admin forms edit both languages.

## Payments

No payments in v1. No currency; emissions are kg CO2e.

## AI

OpenRouter `openrouter/free` only, backend only. Features: assistant chat, report insights,
summaries, structured plans, personalized alternatives, best-effort bill image extraction.
Vision depends on the routed free model; manual entry is always available. AI never invents
emission values. See [ai-features.md](ai-features.md).

## Success criteria for the demo

- A guest can browse content and register.
- A user can record consumption and see a transparent calculated footprint.
- A bill image can be extracted (when the free router supports vision), confirmed, and saved.
- A goal and plan can be created and tracked.
- An admin can see and manage the result, including AI usage.
- The app works in EN and AR, including RTL.
- Seed data makes all of the above possible in under 2 minutes.

Related: #1
