# 01 — Installation

Everything here is **Windows `cmd`** syntax.

## Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | 3.15 | `python --version` |
| Flutter | stable (3.47.9 tested) | `flutter --version` |
| Git | any recent | `git --version` |
| GitHub CLI | any recent | `gh --version` |
| Android SDK / emulator | Flutter-compatible | `flutter doctor` |
| Java | 21 (optional, diagrams) | `java -version` |
| Node.js | 20+ (optional, diagram/screenshot tooling) | `node --version` |

## Backend

```cmd
cd backend
py -3.15 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
copy .env.example .env
python -m flask --app run.py db upgrade
python -m flask --app run.py seed
python run.py
```

- API: `http://127.0.0.1:5000/api/v1/health`
- Swagger: `http://127.0.0.1:5000/api/`
- Admin: `http://127.0.0.1:5000/admin/login`

`py -3.15` is the Windows launcher. If your launcher exposes only `python`, use
`python -m venv .venv` and verify `python --version` is 3.15.

## Mobile

```cmd
cd mobile
flutter pub get
flutter gen-l10n
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:5000/api/v1
```

Android emulator reaches the host through `10.0.2.2`. Physical phone: start the backend with
`HOST=0.0.0.0`, then use the PC LAN IP.

## Tests

```cmd
cd backend
.venv\Scripts\activate
python -m pytest --cov=app --cov-report=term-missing --cov-fail-under=50
```

```cmd
cd mobile
flutter analyze
flutter test --coverage
python ..\scripts\check_lcov.py coverage\lcov.info --min 50
```

## Smoke and demo

From the repository root, with the backend running on port 5001:

```cmd
scripts\smoke.cmd
```

To seed (if needed), start the backend, and open the admin login:

```cmd
scripts\demo.cmd
```

`demo.cmd` starts the backend, opens the admin login, and prints the demo accounts and the
mobile `flutter run` command.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: app` | run from `backend/` |
| `instance/instance/...` DB path | check `DATABASE_URL` resolution against `backend/` |
| Emulator cannot reach backend | use `10.0.2.2`, start with `HOST=0.0.0.0` |
| Arabic text overflows | check RTL layout and shorten the EN/AR map strings |
| L10n key drift | run `mobile/tool/check_l10n.py` from `mobile/`; keys must exist in both maps |
| CI cannot resolve Flutter 3.47.9 | pin or update `flutter-version` in `.github/workflows/mobile.yml` |
| Admin login loop | cookies blocked or `SECRET_KEY` changed; clear cookies and restart |
| AI always disabled | `OPENROUTER_API_KEY` empty; set it in `backend/.env` or use the demo fallbacks |
| Upload fails | check `UPLOAD_FOLDER`, `MAX_CONTENT_LENGTH`, and file type/size |

Related: #2, #3
