# 09 — AI reduction plans

## Purpose

Generate a practical, prioritized reduction plan from the user’s calculated footprint and goal,
with actions, timeline, assumptions, and backend-calculated estimated savings.

## UI (Flutter)

| Screen | Elements |
|---|---|
| `PlansPage` | plan cards (status, goal, action progress), generate button, empty/loading/error |
| `GeneratePlanSheet` | goal selector, preferences (optional), generate, AI/fallback label |
| `PlanDetailPage` | summary, action list grouped by timeframe/priority, checkboxes, estimated savings, assumption link |
| `PlanActionTile` | status, priority, category, due date, saving chip |

States: loading, empty, generating, success, partial, completed, AI disabled, rate limited,
invalid output, failure.

## Screen logic (BLoC)

`PlansBloc`
- Events: `PlansStarted`, `PlanGenerateRequested`, `PlanStatusChanged`,
  `PlanActionStatusChanged`.
- States: `PlansInitial`, `PlansLoading`, `PlansEmpty`, `PlansGenerating`,
  `PlansSuccess(list)`, `PlansDisabled`, `PlansRateLimited`, `PlansFailure`.

`PlanDetailBloc` updates an action and refreshes progress/estimated savings.

## Backend logic

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/v1/plans` | JWT | list |
| POST | `/api/v1/plans/generate` | JWT | AI plan or template fallback |
| GET | `/api/v1/plans/{id}` | JWT | plan + actions |
| PATCH | `/api/v1/plans/{id}` | JWT | status/title |
| PATCH | `/api/v1/plans/{id}/actions/{action_id}` | JWT | action status |
| GET | `/api/v1/plans/{id}/progress` | JWT | completion + estimated savings |

Rules:
- Context: goal baseline/target, top categories, recent records, locale.
- AI output schema validated; `category_key` mapped to real categories; unknown keys rejected.
- **Estimated savings are calculated by the backend** from category emissions × the documented
  action assumption (or a plan-level assumption); AI may suggest a percent but cannot set the
  final number.
- Plan actions are suggestions, not guarantees; label assumptions.
- Template fallback if AI disabled/invalid/rate-limited; labelled “Template plan”.
- Ownership checks; no plan edits to another user’s plan.

## Data

Tables: `reduction_plans`, `plan_actions`, `ai_usage`, `ai_cache`.
Invariants: status machine; action status machine; savings integer grams + assumption text;
AI text separate from calculated savings.

## Acceptance criteria

1. A user can generate a plan for an active goal.
2. The plan has 3–6 actions with priority/timeframe and a documented assumption.
3. Estimated savings are backend-calculated and match the formula shown.
4. AI disabled/429/invalid output produces a template plan with a clear label.
5. Completing actions updates progress and estimated achieved savings.
6. A user cannot access another user’s plan/actions.
7. Plan/action status transitions are valid.
8. EN/AR/RTL are correct; AI text is labelled.

## Tests

| Type | File | Covers |
|---|---|---|
| Service | `tests/modules/plans/test_services.py` | schema mapping, savings calc, status |
| API | `tests/api/test_plans.py` | generate/get/update, ownership, fallback |
| AI mock | `tests/fakes/openrouter.py` | valid/malformed plan JSON |
| Mobile BLoC | `test/features/plans/plans_bloc_test.dart` | generate/success/fallback/failure |
| Widget | `test/features/plans/plan_detail_test.dart` | actions/savings/EN-AR |

## Status

🟡 in progress — issue #11.

Related: #11
