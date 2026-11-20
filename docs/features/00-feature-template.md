# Feature page template

# NN — <Feature name>

## Purpose

<The user problem and the outcome this feature delivers.>

## UI (Flutter)

| Screen | Elements |
|---|---|
| `<ScreenName>` | <list, form, buttons, empty/loading/error states> |

Rules: <validation, limits, disabled states, navigation>.

## Screen logic (BLoC)

`<Feature>Bloc`
- Events: `<Feature>Started`, `<Feature>Submitted`, ...
- States: `Initial`, `Loading`, `Success(data)`, `Failure(message)`
- Emits: <event → state sequence>
- Navigation: <on success / failure>

## Backend logic

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/v1/...` | public/JWT | ... |

Service `<Feature>Service`:
- <rules, permissions, transactions>
- Errors: <codes + HTTP>

Admin (if applicable):
- `/admin/...` — <pages, forms, permissions, audit>

## Data

Tables: `<table>`, `<table>`
Invariants: <...>

## Acceptance criteria

1. ...
2. ...

## Tests

| Type | File | Covers |
|---|---|---|
| Unit | `tests/...` | ... |
| API | `tests/api/...` | ... |
| Widget | `test/...` | ... |

## Status

⬜ / 🟡 / ✅ — issue #<n>, PR #<n>

Related: #<n>
