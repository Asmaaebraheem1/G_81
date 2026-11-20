# Backend — database

## What it is

One SQLite database per backend environment, accessed through SQLAlchemy 2.x and migrated with
Flask-Migrate/Alembic. The schema is documented in `docs/05-data-model.md`.

## Why it exists

The app needs a zero-service, local database with relational integrity, migrations, and
deterministic seed data. SQLite is the fixed choice.

## How it works

- `DATABASE_URL` default: `sqlite:///instance/carbonwise.sqlite3` (resolved against `backend/`).
- `app/core/db.py` creates `db = SQLAlchemy()` and registers a `connect` event:
  `PRAGMA foreign_keys=ON`, `PRAGMA journal_mode=WAL`, `PRAGMA busy_timeout=5000`.
- Models live in `app/modules/<feature>/models.py`; `app/models.py` re-exports every model before
  migrations.
- Alembic runs with `render_as_batch=True` for SQLite ALTER support.
- Services own `db.session.commit()` / `rollback()`; repositories only query.
- Tests use a temporary file DB and dispose the engine.

## Invariants

- Emissions are integer grams CO2e, not floats.
- Factor snapshots are copied onto records.
- `organization_id` is set for organization accounts, null otherwise.
- Soft delete via `status`/`is_active`; no hard delete of records with history.
- Timestamps are UTC.
- User-facing content is `*_en`/`*_ar`.

## How to use it

```cmd
cd backend
.venv\Scripts\activate
python -m flask --app run.py db upgrade
python -m flask --app run.py seed --reset
python -m flask --app run.py seed-info
```

## Testing

`tests/conftest.py` creates a temp SQLite DB, calls `create_app(TestingConfig)`, and yields the
test client. Migration/seed tests run `db upgrade` and `seed` in a temp DB.

## Related

- ADR-0001
- Pages: [data model](../05-data-model.md), [app factory](app-factory.md)
