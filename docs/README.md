# CarbonWise — documentation

CarbonWise is an AI-assisted carbon-footprint tracking and reduction-planning platform for
individuals, households, and organizations. The client app is Flutter (Android, EN + AR/RTL).
The back-office is Flask + Jinja2. The API is Flask `/api/v1` with JWT. The database is SQLite.
AI is OpenRouter `openrouter/free`, backend only.

> Rules for *how we work* live in [`agent.md`](../agent.md), not here.
> This folder answers: **what the product is and how it works.**

## Read in this order (newcomer or agent)

1. [00-overview.md](00-overview.md) — product, actors, flows, scope
2. [03-project-structure.md](03-project-structure.md) — what lives where
3. [04-architecture.md](04-architecture.md) — layers and data flow
4. [05-data-model.md](05-data-model.md) — tables and relations
5. [06-api-reference.md](06-api-reference.md) — endpoints
6. [features/README.md](features/README.md) — one page per feature
7. [01-installation.md](01-installation.md) · [02-configuration.md](02-configuration.md) — run it
8. [testing/strategy.md](testing/strategy.md) · [workflow/process.md](workflow/process.md) — verified and shipped
9. [status.md](status.md) · [changelog.md](changelog.md) — where we are now
10. [demo-script.md](demo-script.md) — the client demo and fallbacks
11. [ai-features.md](ai-features.md) — the AI contract and limitations
12. [diagrams/README.md](diagrams/README.md) · [screenshots/README.md](screenshots/README.md) — required visual deliverables

## Index

| Page | Content |
|---|---|
| [00-overview.md](00-overview.md) | Vision, actors, flows, MVP vs later |
| [01-installation.md](01-installation.md) | Prerequisites, venv, pip, flutter, first run (cmd) |
| [02-configuration.md](02-configuration.md) | Every env var and config key |
| [03-project-structure.md](03-project-structure.md) | Repository tree |
| [04-architecture.md](04-architecture.md) | Backend layers, mobile layers, flows |
| [05-data-model.md](05-data-model.md) | All SQLite tables and rules |
| [06-api-reference.md](06-api-reference.md) | `/api/v1` endpoints, auth, errors |
| [07-roadmap.md](07-roadmap.md) | Milestones and order of work |
| [issues.md](issues.md) | GitHub issue index |
| [ai-features.md](ai-features.md) | AI features, prompts, models, limitations |
| [demo-script.md](demo-script.md) | Client demo, logins, fallbacks |
| [glossary.md](glossary.md) | Domain terms |
| [backend/](backend/) | Flask architecture, database, auth, admin, AI |
| [mobile/README.md](mobile/README.md) | Flutter structure, routes, conventions |
| [features/](features/) | One page per feature |
| [testing/strategy.md](testing/strategy.md) | Test types, mocks, 50% coverage |
| [workflow/process.md](workflow/process.md) | Branch/issue/PR flow |
| [decisions/README.md](decisions/README.md) | ADR index |
| [diagrams/README.md](diagrams/README.md) | Five black-and-white diagrams |
| [screenshots/README.md](screenshots/README.md) | Complete screenshot library |
| [assets/README.md](assets/README.md) | Visual assets + credits |

## Facts that must never drift

| Fact | Value |
|---|---|
| Product | CarbonWise — AI-powered emissions analysis and sustainable reduction planning |
| Customer app | Flutter, Android, BLoC + Dio + sqflite |
| Admin panel | Flask + Jinja2, cookie sessions + CSRF |
| API | Flask, `/api/v1`, JWT, OpenAPI 3 (Swagger `/api/`) |
| Database | SQLite only |
| Languages | English + Arabic (RTL) |
| AI | OpenRouter `openrouter/free` only, backend only, best-effort vision |
| Payments | None in v1 |
| Emissions unit | kg CO2e displayed; integer grams stored |
| Deployment | local demo (`127.0.0.1:5000`, emulator `10.0.2.2:5000`) |
