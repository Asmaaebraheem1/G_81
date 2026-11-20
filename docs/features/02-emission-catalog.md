# 02 — Emission categories & factors

## Purpose

Provide the bilingual activity catalog and the documented emission factors that make every
calculation transparent. Factors are versioned by source, region, unit, and validity; records keep
a snapshot so history is stable.

## UI (Flutter)

| Screen | Elements |
|---|---|
| `CategoryPicker` | category cards with icon/image, name, unit hint, description |
| `FactorPicker` | factor list filtered by category, name, unit, source/year, active only |
| `CategoryDetailPage` | category description, factors, recent records, tips |
| `FactorInfoSheet` | factor value, unit, source name/URL/year, region, validity, notes |

States: loading, empty (no factors), success, error, disabled category.

## Screen logic (BLoC)

`CatalogBloc`
- Events: `CatalogStarted`, `CategorySelected`, `FactorSelected`, `CatalogRefreshed`.
- States: `CatalogInitial`, `CatalogLoading`, `CatalogSuccess(categories, factors)`,
  `CatalogEmpty`, `CatalogFailure(message)`.
- Caches the catalog in sqflite for offline display.
- `CategorySelected` triggers a factor fetch; `FactorSelected` publishes the factor to the record
  form.

## Backend logic

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/v1/categories` | public | active categories, ordered |
| GET | `/api/v1/categories/{id}` | public | category detail |
| GET | `/api/v1/factors?category_id=` | public | active factors |
| GET | `/api/v1/factors/{id}` | public | factor + source |

Rules:
- Only `is_active` categories/factors are public.
- A factor unit must match the record unit; the service rejects mismatches.
- Factor `factor_grams_co2e` is a positive integer; 0 is allowed only for explicitly zero-emission
  activities.
- The admin CRUD for categories/factors lives in feature 14.
- Deactivating a factor does not change existing records (snapshots).

## Data

Tables: `emission_categories`, `emission_factors`.
Invariants: unique `key`, bilingual names, positive factor, source/region/validity required,
records snapshot the factor.

## Acceptance criteria

1. Public category/factor lists return only active, ordered rows.
2. A factor detail exposes source name/URL/year, region, unit, and validity.
3. Selecting a category filters factors correctly.
4. A record cannot use a factor from another category or a mismatched unit.
5. Deactivating a factor hides it from new records but leaves existing records unchanged.
6. The catalog is cached for offline display and shows an offline banner.
7. EN and AR names render correctly; RTL layout is intact.

## Tests

| Type | File | Covers |
|---|---|---|
| Service | `tests/modules/catalog/test_services.py` | active filters, unit/category rules |
| API | `tests/api/test_catalog.py` | public lists, detail, 404, inactive |
| Mobile BLoC | `test/features/catalog/catalog_bloc_test.dart` | load/empty/failure |
| Widget | `test/features/catalog/category_picker_test.dart` | EN/AR rendering |

## Status

🟡 in progress — issue #6.

Related: #6
