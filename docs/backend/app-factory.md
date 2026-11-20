# Backend — application factory

## What it is

The Flask application is built by `create_app(config_object)` in `backend/app/__init__.py`.
It registers configuration, extensions, blueprints, error handlers, CLI commands, and the admin
shell. No global app object performs work at import time.

## Why it exists

Tests need isolated app instances with temporary SQLite databases; the CLI needs a configured app
for migrations/seed; the admin and API share services without sharing auth mechanisms.

## How it works

```
run.py → create_app(Config) → app
                           ├── core/config.py
                           ├── core/db.py (SQLAlchemy + PRAGMAs)
                           ├── core/errors.py (JSON/HTML handlers)
                           ├── api/v1 blueprint
                           ├── admin blueprint
                           └── CLI: seed, seed-info, reset-demo
```

- `Config`, `TestingConfig`, and `DevelopmentConfig` live in `core/config.py`.
- Relative `DATABASE_URL` paths resolve against `backend/`, never the process CWD.
- A startup guard rejects non-SQLite URLs and any model other than `openrouter/free`.
- Blueprints are registered once; modules import `db` from `core.db`.

## How to use it

```cmd
cd backend
.venv\Scripts\activate
python run.py
```

```cmd
python -m flask --app run.py db upgrade
python -m flask --app run.py seed --reset
```

## Testing

`tests/conftest.py` creates a temporary SQLite file, calls `create_app(TestingConfig)`, and
disposes the engine after the app context. See `docs/testing/strategy.md`.

## Related

- ADR-0001
- Pages: [database](database.md), [api](api.md), [authentication](authentication.md)
