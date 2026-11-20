# 03 — Project structure

```
G_81/
├── agent.md                     # rules: how we work
├── AGENTS.md                    # auto-loaded pointer to agent.md
├── INTAKE.md                    # approved Phase 0 intake
├── docs/                        # documentation, diagrams, screenshots, assets
│   ├── diagrams/                # 5 B&W PNGs + generate_diagrams.py
│   ├── screenshots/             # mobile EN/AR + admin library
│   └── assets/                  # 15 WebP illustrations + credits
├── .pi/skills/                  # github-workflow, project-docs, skill-authoring
├── .github/
│   ├── workflows/               # backend.yml, mobile.yml
│   ├── ISSUE_TEMPLATE/          # feature.yml, bug.yml, config.yml
│   └── PULL_REQUEST_TEMPLATE.md
├── scripts/
│   ├── check_lcov.py            # mobile line-coverage gate
│   ├── smoke.py / smoke.cmd     # API smoke test (21 checks)
│   ├── demo.cmd                 # local demo launcher
│   └── generate_diagrams.py     # wrapper for docs/diagrams generator
├── backend/
│   ├── .venv/                   # local, git-ignored
│   ├── app/
│   │   ├── __init__.py          # create_app()
│   │   ├── cli.py               # flask init-db / flask seed
│   │   ├── models.py            # re-exports all ORM models
│   │   ├── seed.py              # deterministic demo dataset
│   │   ├── core/                # config, db, errors, emissions, security, responses
│   │   ├── modules/             # auth, users, organizations, catalog, records,
│   │   │                        # documents, reports, goals, plans, alternatives,
│   │   │                        # challenges, notifications, ai, content, admin
│   │   ├── api/v1/              # 134 JSON + JWT routes
│   │   ├── templates/           # admin Jinja pages + error pages
│   │   └── static/
│   │       ├── css/admin.css
│   │       ├── js/admin.js
│   │       └── assets/images/   # same 15 WebP illustrations
│   ├── migrations/              # Alembic (single v1 revision)
│   ├── tests/                   # unit, integration, API, admin
│   ├── instance/                # SQLite DB + private uploads (git-ignored)
│   ├── .env.example
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pyproject.toml           # ruff/black/pytest config
│   └── run.py                   # local entrypoint
└── mobile/
    ├── lib/
    │   ├── main.dart
    │   ├── core/                # config, network, database, models, localization,
    │   │                        # navigation, storage, theme, shared widgets
    │   └── features/<feature>/  # presentation + data for one feature
    ├── assets/images/           # committed visual assets
    ├── test/                    # unit + widget tests
    ├── tool/                    # l10n/UI development helpers
    ├── analysis_options.yaml
    └── pubspec.yaml
```

## Ownership rules

- `backend/app/core` — shared infrastructure only; no feature logic.
- `backend/app/modules/<x>` — one feature; cross-module access only through public service functions.
- `backend/app/templates` — presentation; no SQL/business logic.
- `backend/app/static` — CSS/JS/images; no runtime secrets.
- `mobile/lib/core` — cross-cutting only; no feature UI.
- `mobile/lib/features/<x>` — data/domain/presentation for one feature.
- `docs/` — describes the code; never a second source of truth for behaviour.
- `scripts/` — dev/demo helpers; no production secrets; cmd-compatible entrypoints.
- `docs/diagrams`, `docs/screenshots`, `docs/assets` — required deliverables, not scratch space.

Related: #2, #3
