# Architecture decisions (ADR)

One file per decision that is expensive to reverse. Format: Context → Decision → Consequences →
Alternatives.

| ADR | Decision | Status |
|---|---|---|
| [0001](ADR-0001-sqlalchemy-over-raw-sqlite.md) | SQLAlchemy 2.x ORM over raw SQLite | accepted |
| [0002](ADR-0002-ai-model-policy.md) | OpenRouter `openrouter/free` only; best-effort vision | accepted |
| [0003](ADR-0003-bilingual-data-strategy.md) | ARB + `*_en`/`*_ar` bilingual strategy | accepted |
| [0004](ADR-0004-private-upload-storage.md) | Private filesystem uploads, authenticated download | accepted |
| [0005](ADR-0005-auth-split.md) | JWT for API, cookie sessions for admin | accepted |

## When to write one

- database/access layer
- auth scheme
- payment model
- AI model/policy
- bilingual data strategy
- file storage
- deployment

## Rules

- Number sequentially: `ADR-000N-<kebab-slug>.md`.
- Never edit an accepted ADR to change its meaning; write a new one that supersedes it.
- Link the ADR from the affected docs page and the PR.
