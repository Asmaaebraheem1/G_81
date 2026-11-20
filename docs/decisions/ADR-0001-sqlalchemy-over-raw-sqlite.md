# ADR-0001 — SQLAlchemy 2.x ORM over raw SQLite

- **Status:** accepted
- **Date:** 2026-11-19
- **Deciders:** owner + agent

## Context

The fixed stack requires SQLite only, Flask, Flask-SQLAlchemy, Flask-Migrate/Alembic, and
parameterized access. The domain has ~29 tables with ownership, snapshots, and audit rules.
Raw `sqlite3` would make migrations, relations, and test isolation risky.

## Decision

Use SQLAlchemy 2.x ORM models with Flask-SQLAlchemy, and Alembic migrations via Flask-Migrate with
`render_as_batch=True`. Repositories are the only layer that talks to the ORM. Raw `sqlite3` is
limited to PRAGMAs/edge cases.

## Consequences

### Positive
- Typed models, relations, and a single session lifecycle.
- Alembic handles schema changes; batch mode covers SQLite ALTER limits.
- Tests can use a temporary SQLite file and create/drop cleanly.

### Negative / trade-offs
- ORM overhead is acceptable for a local demo.
- Contributors must respect the route → service → repository layering.

### Follow-ups
- Keep `models.py` imports centralized before migrations.
- Enforce `PRAGMA foreign_keys=ON` and WAL on every connection.

## Alternatives considered

| Alternative | Why not |
|---|---|
| Raw `sqlite3` | No migrations/relations; high risk of unsafe SQL and duplicated mapping |
| Another ORM (peewee, Tortoise) | Not in the fixed stack |
| Another database | Forbidden by the stack |

Related: #4
