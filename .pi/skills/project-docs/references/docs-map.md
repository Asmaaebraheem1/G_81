# docs/ map (Laravel-style, multi-file)

Structure generated with the project — keep this file and `docs/README.md` in sync.

```
docs/
├── README.md                     # index + read-in-this-order path
├── status.md                     # current state: done / in progress / missing
├── changelog.md                  # user-visible changes, newest first, with issue links
├── glossary.md                   # project terms, abbreviations, domain language
│
├── 00-overview.md                # what the product is, who uses it, main flows
├── 01-installation.md            # prerequisites, venv, pip, flutter pub, .env, first run
├── 02-configuration.md           # every env var + config key, defaults, effect
├── 03-project-structure.md       # repo tree, what lives where, why
├── 04-architecture.md            # layers, module boundaries, data flow, diagram
├── 05-data-model.md              # all SQLite tables and rules
├── 06-api-reference.md           # /api/v1 endpoints, auth, errors
├── 07-roadmap.md                 # milestones and order of work
├── ai-features.md                # AI feature contract, models, limitations
├── issues.md                     # GitHub issue index
├── demo-script.md                # client demo, logins, fallbacks
├── assets/
│   ├── README.md                 # visual asset index
│   └── credits.md                # sources and licenses
├── diagrams/
│   └── README.md                 # five B&W diagrams + sources
├── screenshots/
│   ├── README.md                 # screenshot coverage matrix
│   ├── mobile/
│   └── admin/
│
├── backend/
│   ├── app-factory.md            # create_app, blueprints, module registration
│   ├── database.md               # SQLite, SQLAlchemy models, migrations, PRAGMAs
│   ├── services-and-repositories.md
│   ├── api.md                    # conventions, errors, pagination, versioning
│   ├── authentication.md         # JWT for API, cookie sessions for admin
│   ├── admin-panel.md            # Jinja views, forms, CSRF
│   ├── ai-integration.md         # OpenRouter, openrouter/free, prompts, errors
│   └── error-handling.md
│
├── mobile/
│   ├── README.md                 # Flutter structure, routes, conventions, commands
│   ├── app-architecture.md       # feature-first layout, layers, DI
│   ├── bloc.md                   # events, states, freezed, patterns
│   ├── networking.md             # Dio client, interceptors, refresh, errors
│   ├── local-database.md         # sqflite, versions, migrations, sync rules
│   ├── navigation.md
│   └── secure-storage.md         # flutter_secure_storage, token lifecycle
│
├── testing/
│   ├── strategy.md               # what is tested where, why, mocks policy
│   ├── backend-testing.md        # pytest, fixtures, temp SQLite
│   ├── mobile-testing.md         # bloc_test, widget, integration_test
│   └── coverage.md               # 50% rule, how it is measured/enforced
│
├── workflow/
│   ├── branches.md               # main + dev/<issue>-<slug>
│   ├── issues.md                 # templates, splitting, linking
│   ├── pull-requests.md          # review gates, merge policy
│   └── process.md                # the 9 steps in practice
│
├── features/
│   ├── README.md                 # index + status table
│   └── NN-<feature>.md           # one page per feature
│
└── decisions/
    ├── README.md                 # ADR index
    └── ADR-000N-<slug>.md        # expensive-to-reverse decisions
```

## Rules for this map

- Flat topic files at the root for cross-cutting things; one folder per area (`backend/`, `mobile/`, `testing/`, `workflow/`).
- Any page may be split when it exceeds ~200 lines of content.
- A page that no longer matches the code is a bug — fix it in the same PR.
