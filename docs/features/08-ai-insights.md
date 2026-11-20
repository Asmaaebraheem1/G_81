# 08 — AI insights & summaries

## Purpose

Explain the calculated report: top sources, unusual changes, category comparisons, reduction
opportunities, and a plain-language sustainability summary.

## UI (Flutter)

| Screen | Elements |
|---|---|
| `InsightsPage` | period selector, insight cards (top sources, changes, comparisons, opportunities), generate/refresh, “Calculated context” chip |
| `SummaryCard` | AI summary text, copy, disclaimer |
| `InsightDetailSheet` | narrative + source values + report link |

States: initial, loading, success, insufficient data, disabled, rate limited, invalid output,
failure.

## Screen logic (BLoC)

`InsightsBloc`
- Events: `InsightsStarted`, `InsightsPeriodChanged`, `InsightsGenerateRequested`,
  `SummaryRequested`.
- States: `InsightsInitial`, `InsightsLoading`, `InsightsInsufficientData`,
  `InsightsSuccess(insights)`, `InsightsDisabled`, `InsightsRateLimited`, `InsightsFailure`.

The UI renders calculated cards (from the API) separately from AI narrative cards.

## Backend logic

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/v1/ai/insights` | JWT | structured insights |
| POST | `/api/v1/ai/summary` | JWT | narrative summary |

Rules:
- Context: period totals, category shares, previous-period comparison, top activities, goal progress.
- Output schema validated; numeric fields must match backend values (server overwrites/copies).
- Insufficient data (< 3 records or no comparison period) returns `insufficient_data` and a
  calculated explanation, not an AI hallucination.
- Cache by context hash; usage recorded; no prompt logs.
- Fallback: rules-based top sources/change text labelled “Calculated fallback”.

## Data

Tables: `ai_usage`, `ai_cache`; read-only computed data from records/reports/goals.
Invariants: AI never owns a number; calculated values are copied server-side.

## Acceptance criteria

1. Insights identify top sources and changes that match the report.
2. The response includes `calculated_context` and AI narrative separately.
3. Insufficient data returns a helpful state, not invented insights.
4. AI disabled/429/invalid JSON produce typed errors and a fallback.
5. Summaries contain no numbers that differ from the calculated totals.
6. EN/AR output and RTL layout are correct.
7. Usage metadata is recorded; no prompts are logged.

## Tests

| Type | File | Covers |
|---|---|---|
| Service | `tests/modules/ai/test_insights.py` | context, schema, numeric guard, fallback |
| API | `tests/api/test_ai_insights.py` | success/insufficient/disabled/invalid |
| Mobile BLoC | `test/features/insights/insights_bloc_test.dart` | success/insufficient/failure |
| Widget | `test/features/insights/insights_page_test.dart` | calculated vs AI cards, EN/AR |

## Status

🟡 in progress — issue #18.

Related: #18
