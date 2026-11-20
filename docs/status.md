# Status

Current state of the project. Update in the same PR as the change.

## Milestone

**M10 — Hardening & deliverables** (final phase)

## Features

| Feature | Backend | Mobile | Admin | Docs | Status |
|---|---|---|---|---|---|
| F01 Accounts, profiles & preferences | ✅ | ✅ | ✅ | ✅ | ✅ |
| F02 Emission categories & factors | ✅ | ✅ | ✅ | ✅ | ✅ |
| F03 Consumption records & calculation | ✅ | ✅ | ✅ | ✅ | ✅ |
| F04 Bill/document uploads & AI extraction | ✅ | ✅ | ✅ | ✅ | ✅ |
| F05 Dashboard, reports & export | ✅ | ✅ | ✅ | ✅ | ✅ |
| F06 Sustainability goals | ✅ | ✅ | ✅ | ✅ | ✅ |
| F07 AI sustainability assistant | ✅ | ✅ | ✅ | ✅ | ✅ |
| F08 AI insights & summaries | ✅ | ✅ | ✅ | ✅ | ✅ |
| F09 AI reduction plans | ✅ | ✅ | ✅ | ✅ | ✅ |
| F10 Sustainable alternatives | ✅ | ✅ | ✅ | ✅ | ✅ |
| F11 Challenges, achievements & leaderboard | ✅ | ✅ | ✅ | ✅ | ✅ |
| F12 Notifications & reminders | ✅ | ✅ | ✅ | ✅ | ✅ |
| F13 Admin core, users & organizations | — | — | ✅ | ✅ | ✅ |
| F14 Admin catalog, records & documents | — | — | ✅ | ✅ | ✅ |
| F15 Admin programs, content, analytics & AI | — | — | ✅ | ✅ | ✅ |

`—` means the feature is intentionally admin-only and has no `/api/v1` surface.

## Verification (latest — 2026-11-20)

| Check | Result |
|---|---|
| Backend tests | **54 passed**, 0 failed |
| Backend coverage | **76%** (`pytest --cov=app`, gate ≥ 50%) |
| Mobile tests | **23 passed** (`flutter test --coverage`) |
| Mobile coverage | **92.2%** (268 lines, gate ≥ 50%) |
| Ruff / Black | clean (`ruff check`, `black --check`, 95 files) |
| Flutter analyze | **0 errors**; 23 info-level lints remain |
| L10n parity | **310 EN / 310 AR** keys, no gaps (`mobile/tool/check_l10n.py`) |
| CI | workflows committed; first run happens after the repository is pushed |
| Smoke script | `scripts/smoke.cmd` passes 21 checks against the running backend (health, login, auth/me, catalog, records, goals, dashboard, AI status, 401, admin login) |
| Demo | `docs/demo-script.md` verified against the running app |
| Diagrams | five 300 DPI black-and-white PNGs + editable generator in `docs/diagrams/` |
| Screenshots | 29 admin + 27 EN + 26 AR mobile images; remaining state gaps are listed in `docs/screenshots/README.md` |
| Visual assets | 15 original WebP illustrations in both mobile and admin asset folders, with credits in `docs/assets/credits.md` |

## Known gaps

- Failure/loading/empty screenshot variants and the Arabic welcome/register
  screens are not captured yet; see the gap table in `docs/screenshots/README.md`.
- 23 info-level analyzer lints remain across four style rules
  (`use_build_context_synchronously`, `unnecessary_string_interpolations`,
  `prefer_initializing_formals`, `use_null_aware_elements`); there are **0 errors**
  and they are tracked for cleanup.
- The OpenRouter key is intentionally blank in the demo environment, so AI
  screens are captured in deterministic fallback mode (`ai_disabled` /
  rules-based summaries). Production deployment requires a server-side key.
- GitHub issues/PRs are created in the repository workflow; the local demo
  remains the source of truth until the remote is published.

## Next

1. Publish the repository and run both CI workflows green on PR #1.
2. Regenerate the deferred screenshot variants at the next UI freeze (emulator intentionally
   stopped on the low-resource development machine).
3. Record the final demo walkthrough and attach it to the release notes.

Related: #1
