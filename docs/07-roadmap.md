# 07 — Roadmap

Order of work = order of GitHub issues (`docs/issues.md`). One milestone = one or more issues;
one issue = one branch = one PR.

| Milestone | Issue(s) | Definition of done |
|---|---|---|
| **M0 — Foundation** | #3 backend scaffold · #4 mobile scaffold | health endpoint + localized app shell + test suites run |
| **M1 — Data** | #5 schema, migrations, seed | `db upgrade` + `seed` create all tables + demo data |
| **M2 — Auth** | #6 | register/login/refresh/logout; tokens in secure storage; guest path works |
| **M3 — Catalog & records** | #7, #8 | categories/factors + records + transparent calculation |
| **M4 — Documents & reports** | #9, #10 | upload/extract/confirm + dashboard/reports/export |
| **M5 — Goals & plans** | #11, #12 | goals + AI/template plans + action tracking |
| **M6 — Alternatives & engagement** | #13, #14, #15 | alternatives, challenges/badges/leaderboard, notifications |
| **M7 — Admin core** | #16 | cookie login, dashboard, users/orgs, settings, audit |
| **M8 — Admin management** | #17, #18 | catalog/records/documents + programs/content/AI monitoring |
| **M9 — AI** | #19 | assistant/insights/summary/flags, budgeted, mocked, graceful fallback |
| **M10 — Hardening & deliverables** | #20, #21 | coverage ≥ 50%, EN/AR audit, demo, diagrams, screenshots, assets, AI docs |

## Order rules

- Data before features; auth before ownership; domain before AI.
- AI needs real calculated data — never first.
- Admin core follows the domain it manages.
- Every milestone is demoable; no "big bang" at the end.
- Diagrams/ERD can be drafted early; the final screenshot set is produced at UI freeze.

## Definition of done (per issue)

Acceptance criteria met · tests added · coverage ≥ 50% per side · docs updated · lint/analyze
clean · review done · CI green.

## Risks

| Risk | Mitigation |
|---|---|
| Scope grows | v1 feature list fixed in `00-overview.md`; extras go to "Later" |
| AI free router changes/limits | typed errors, rules/template fallbacks, usage monitoring, no paid fallback |
| Vision unavailable | manual entry is the primary fallback; consent notice |
| Flutter/CI version mismatch | pin 3.47.9 in the workflow; update the pin and record the change when the SDK moves |
| Screenshot volume | deterministic screenshot mode + coverage matrix; capture at UI freeze |
| SQLite concurrency | WAL mode, short transactions, single-process local demo |
| Bilingual content drift | `*_en`/`*_ar` required in forms and seed; ARB checks |

Related: #1
