# 10 — Sustainable alternatives

## Purpose

Present practical lower-emission alternatives (public transport, efficiency, reuse, recycling,
water/energy savings) and personalize them with AI while keeping impact estimates calculated and
documented.

## UI (Flutter)

| Screen | Elements |
|---|---|
| `AlternativesPage` | catalog grid/list, category filter, search, impact badge, saved/accept |
| `AlternativeDetailPage` | description, assumption, estimated impact, source, save/accept/dismiss, add to plan |
| `RecommendedAlternatives` | AI-personalized section, rationale, fallback label |

States: loading, empty, success, filtered empty, saving, saved/accepted, AI disabled/rate limited,
failure.

## Screen logic (BLoC)

`AlternativesBloc`
- Events: `AlternativesStarted`, `AlternativesFilterChanged`, `AlternativeSaved`,
  `RecommendedRequested`.
- States: `AlternativesInitial`, `AlternativesLoading`, `AlternativesEmpty`,
  `AlternativesSuccess(list)`, `AlternativesSaving`, `AlternativesFailure`.

Recommended list merges AI-selected IDs with the catalog; unknown IDs are dropped server-side.

## Backend logic

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/v1/alternatives` | public | active catalog |
| GET | `/api/v1/alternatives/{id}` | public | detail |
| GET | `/api/v1/alternatives/recommended` | JWT | AI + catalog personalization |
| GET | `/api/v1/alternatives/saved` | JWT | saved/accepted |
| POST | `/api/v1/alternatives/{id}/save` | JWT | save/accept/dismiss |

Rules:
- Impact estimate = `category_emissions_grams × estimated_reduction_percent / 100` for the period,
  or a documented per-action assumption; labelled as an estimate.
- AI selects IDs + rationale only; backend validates IDs and computes impact.
- Fallback: top-category catalog alternatives labelled “Curated”.
- No invented IDs, percentages, or sources.
- Ownership on saved alternatives.

## Data

Tables: `alternatives`, `saved_alternatives`, `ai_usage`, `ai_cache`.
Invariants: documented `assumption_en/ar`, source, percent 0–100; saved unique per user/alternative.

## Acceptance criteria

1. A user can browse/filter alternatives and see documented assumptions.
2. Saving/accepting/dismissing updates the saved list.
3. Recommendations return only valid catalog IDs and a rationale.
4. Estimated impact is backend-calculated and matches the assumption.
5. AI disabled/429 produces a curated fallback, clearly labelled.
6. A user cannot see another user’s saved list.
7. EN/AR content and RTL layout are correct.
8. No AI-invented percentages or sources are rendered.

## Tests

| Type | File | Covers |
|---|---|---|
| Service | `tests/modules/alternatives/test_services.py` | validation, impact calc, save state |
| API | `tests/api/test_alternatives.py` | catalog/recommended/save, ownership |
| Mobile BLoC | `test/features/alternatives/alternatives_bloc_test.dart` | load/save/fallback |
| Widget | `test/features/alternatives/alternatives_page_test.dart` | filter/save/EN-AR |

## Status

🟡 in progress — issue #12.

Related: #12
