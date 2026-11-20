# Testing strategy

## Rule

Coverage **≥ 50%** on each side, measured separately. Below 50% = not done. CI enforces it.

## Backend

| Type | Tool | What it proves |
|---|---|---|
| Unit | pytest | services, validators, calculation engine, AI parsing |
| Integration | pytest + temp SQLite | repositories, transactions, migrations, seed |
| API/contract | Flask test client | status codes, shapes, auth, validation, ownership |

- Fresh temporary SQLite per test session/module; no shared state; no network.
- `TestingConfig` blanks the AI key and uses a mocked OpenRouter client.
- Upload tests use `tmp_path`, never the real `instance/uploads`.
- Run: `python -m pytest --cov=app --cov-report=term-missing --cov-fail-under=50`.

## Mobile

| Type | Tool | What it proves |
|---|---|---|
| Unit | `bloc_test`, `mocktail` | BLoC sequences, repositories, mappers, formatters |
| Widget | `flutter_test` | screens render loading/success/empty/failure; RTL smoke |
| Integration | `integration_test` | login → dashboard → add record → report; EN/AR switch |

- No `pumpAndSettle()` while a spinner may run; use explicit `pump()`.
- Tall test surface for lazy scrollable forms.
- Fake API/local repositories; no real network or secure storage.
- Run: `flutter test --coverage` + `python ..\scripts\check_lcov.py coverage\lcov.info --min 50`.

## Cross-cutting

- Every BLoC: success and failure/empty sequences asserted.
- Every endpoint: one happy path + one error path (auth/validation/ownership/AI error).
- Calculation engine: property-style table tests for quantity × factor, rounding, snapshots.
- Bug fix: failing test first, then the fix.
- Manual smoke before "done": `scripts\smoke.cmd`.

## AI mocks

- `tests/fakes/openrouter.py` returns deterministic chat/JSON/vision responses.
- Cases: success, 429, timeout, empty content, malformed JSON, vision unavailable.
- Assert no real network call; assert `ai_usage` rows and no prompt text in logs.
- Mobile: fake AI repository; assert `AiFailure` states and fallback UI.

## Coverage reports

| Side | Command | Artifact |
|---|---|---|
| Backend | `pytest --cov=app --cov-report=xml --cov-report=term-missing` | `backend/coverage.xml` |
| Mobile | `flutter test --coverage` | `mobile/coverage/lcov.info` |

CI uploads both artifacts. The mobile gate parses `LF:`/`LH:` lines with
`scripts/check_lcov.py`.

## CI

- `backend.yml` and `mobile.yml` run on every PR to `main`/`dev/**`.
- Both must be green before merge.
- No OpenAI/OpenRouter key in CI; a secret-scan step checks the repo.
- Flutter version is pinned to 3.47.9; if unavailable, the workflow falls back to `channel: stable`
  and the difference is recorded here.

## Anti-patterns

- Tests that only assert "no exception".
- Mocking the code under test.
- Real network calls in tests.
- Ignoring a flaky test instead of fixing it.
- Screenshots used as the only proof of a working UI.

Related: #2, #3, #19
