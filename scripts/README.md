# Scripts

Developer and demo helpers. Run everything from the repository root unless noted.

| Script | Purpose |
|---|---|
| `demo.cmd` | Seeds the SQLite demo database if needed, starts Flask on `127.0.0.1:5001`, opens the admin login, and prints demo accounts. |
| `smoke.cmd` / `smoke.py` | End-to-end smoke test against a running backend: health, login, `/auth/me`, catalog, records, goals, dashboard, AI status, anonymous 401, admin login page. |
| `check_lcov.py` | Parses an LCOV file and enforces the 50% line-coverage gate. Used by `mobile.yml` and locally. |
| `generate_diagrams.py` | Convenience wrapper that regenerates the five B&W diagrams from `docs/diagrams/generate_diagrams.py`. |

## Demo

```cmd
scripts\demo.cmd
```

The backend listens on **5001** because port 5000 is commonly occupied on the
development machine. Do not change the port without updating the mobile
`API_BASE_URL` command.

## Smoke

With the backend already running:

```cmd
scripts\smoke.cmd
```

or with a different base URL:

```cmd
backend\.venv\Scripts\python.exe scripts\smoke.py --base http://127.0.0.1:5001/api/v1
```

The smoke test uses only the Python standard library and exits non-zero on the first
failed check.

## Coverage gate

```cmd
cd mobile
flutter test --coverage
cd ..
backend\.venv\Scripts\python.exe scripts\check_lcov.py mobile\coverage\lcov.info --min 50
```

Backend coverage is enforced by `pytest --cov-fail-under=50` in `backend.yml`.

## Diagrams and assets

```cmd
backend\.venv\Scripts\python.exe scripts\generate_diagrams.py
backend\.venv\Scripts\python.exe docs\assets\generate_assets.py
```

Both generators are deterministic and overwrite their committed outputs. See
`docs/diagrams/README.md` and `docs/assets/README.md` for the file inventory,
design rules, and credits.
