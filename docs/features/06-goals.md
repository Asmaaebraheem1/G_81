# 06 — Sustainability goals

## Purpose

Let users set a percentage reduction target for a week, month, or year, with a stored baseline and
live progress based on backend-calculated emissions.

## UI (Flutter)

| Screen | Elements |
|---|---|
| `GoalsPage` | list with status chips, period filter, empty/loading/error |
| `GoalFormPage` | title, target %, period type, start/end, baseline preview, save |
| `GoalDetailPage` | baseline vs current vs target, progress ring, status, linked plans, edit/cancel |
| `GoalProgressCard` | home/report card with on-track/behind/missed |

States: loading, empty, success, validation error, saving, completed, missed, cancelled,
delete confirmation.

## Screen logic (BLoC)

`GoalsBloc`
- Events: `GoalsStarted`, `GoalsFilterChanged`, `GoalSubmitted`, `GoalCancelled`.
- States: `GoalsInitial`, `GoalsLoading`, `GoalsEmpty`, `GoalsSuccess(list)`,
  `GoalsSubmitting`, `GoalsFailure(fieldErrors)`.

`GoalDetailBloc` loads progress and linked plans; on action completion it refreshes progress.

## Backend logic

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/v1/goals` | JWT | list own goals |
| POST | `/api/v1/goals` | JWT | create + compute baseline/target |
| GET | `/api/v1/goals/{id}` | JWT | detail |
| PATCH | `/api/v1/goals/{id}` | JWT | edit title/dates/status |
| DELETE | `/api/v1/goals/{id}` | JWT | cancel/soft delete |
| GET | `/api/v1/goals/{id}/progress` | JWT | baseline/current/target progress |

Rules:
- `target_percent` 1–100; dates valid; period length matches type (week 7 days, month calendar
  month, year calendar year).
- Baseline is the equivalent period immediately before `start_date` (or an explicit baseline
  range); stored at creation.
- `target_emissions_grams = round(baseline × (1 − target_percent/100))`.
- Progress = current emissions in `[start,end]` vs baseline; status updates when the end date passes.
- Ownership checks.
- A goal can link to plans but does not require one.
- No AI-generated numbers; AI may suggest a goal in text but the user sets the value.

## Data

Table: `goals`.
Invariants: baseline snapshot, target snapshot, status machine, user/org ownership.

## Acceptance criteria

1. A user can create weekly/monthly/yearly goals with valid dates.
2. The baseline and target are computed and stored at creation.
3. Progress uses calculated emissions and matches the report totals.
4. A goal becomes completed/missed after its end date based on progress.
5. A user cannot access another user’s goal.
6. Editing dates recomputes baseline/target or rejects unsafe changes.
7. Cancelling a goal is a soft delete and keeps history.
8. Empty/loading/error states and EN/AR/RTL are correct.

## Tests

| Type | File | Covers |
|---|---|---|
| Service | `tests/modules/goals/test_services.py` | baseline/target, progress, status |
| API | `tests/api/test_goals.py` | CRUD, validation, ownership |
| Mobile BLoC | `test/features/goals/goals_bloc_test.dart` | list/create/failure |
| Widget | `test/features/goals/goal_form_test.dart` | validation/EN-AR |

## Status

🟡 in progress — issue #10.

Related: #10
