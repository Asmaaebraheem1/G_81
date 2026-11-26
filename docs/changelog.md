# Changelog

User-visible changes, newest first. Link the issue and PR.

## Unreleased

- **docs(report)**: Arabic RTL Word project report covering the idea, features,
  technology choices, diagrams, AI guardrails and verification evidence (#24).
- **feat(mobile)**: complete EN/AR UI with RTL bidi handling for numerics, factors,
  plans, alternatives, insights, challenges, leaderboard, documents, and content.
- **feat(mobile)**: bilingual status/category labels, localized `kg` units, and
  login validation that accepts all seeded demo passwords.
- **fix(backend)**: natural Arabic/English change phrases in AI fallback narratives.
- **docs**: full status, changelog, screenshot index, and AI-vs-backend ownership notes.
- **test**: backend 54 passing / 76% coverage; mobile 23 passing / 92.2% coverage.
- **ci**: `backend.yml` (ruff, black, pytest + coverage gate) and `mobile.yml`
  (analyze, tests, lcov gate); issue/PR templates included.
- **feat(scripts)**: `demo.cmd`, `smoke.cmd`/`smoke.py` (21 checks), and
  `check_lcov.py` coverage gate.
- **docs(diagrams)**: five 300 DPI black-and-white diagrams and the editable
  Pillow generator (`docs/diagrams/generate_diagrams.py`).
- **docs(assets)**: 15 original flat WebP illustrations with provenance and
  credits (`docs/assets/README.md`, `credits.md`).
- **docs**: final post-merge status, issue index (#1–#22), CI evidence, and
  remaining screenshot gaps.
- **chore**: project scaffolding, CI workflows, issue/PR templates, scripts.
- **feat(core)**: CarbonWise backend, mobile app, admin dashboard, and AI integration.

## 2026-11-19 — Phase 0 / Phase 1

- **docs**: `INTAKE.md` approved with CarbonWise scope, 15 features, AI policy, and deliverables.
- **chore**: `agent.md`, `AGENTS.md`, `.gitignore`, and the three project skills created.
- **docs**: multi-file documentation set and feature pages created.

<!-- Keep entries short. One line per user-visible change. -->
