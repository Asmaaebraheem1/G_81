# 03 — Consumption records & calculation engine

## Purpose

Let users record electricity, gas/fuel, road transport, flights, water, household/business
activities, and waste, and calculate estimated emissions transparently with a factor snapshot and
a readable formula.

## UI (Flutter)

| Screen | Elements |
|---|---|
| `RecordsPage` | search, category filter, date range, list, total, empty/loading/error |
| `RecordFormPage` | category → factor → quantity/unit → date → notes; live estimate preview; save |
| `RecordDetailPage` | quantity, factor, source/year, formula, emissions kg, attachment, edit/delete |
| `CalculationSheet` | step-by-step formula and snapshot source |

States: loading, empty, success, validation error, saving, save success, save failure, delete
confirmation, offline cache.

## Screen logic (BLoC)

`RecordsBloc`
- Events: `RecordsStarted`, `RecordsFilterChanged`, `RecordsRefreshed`, `RecordDeleted`.
- States: `RecordsInitial`, `RecordsLoading`, `RecordsEmpty`, `RecordsSuccess(records, meta)`,
  `RecordsFailure(message)`.

`RecordFormBloc`
- Events: `RecordFormStarted`, `RecordCategoryChanged`, `RecordFactorChanged`,
  `RecordQuantityChanged`, `RecordSubmitted`, `RecordDeleted`.
- States: `RecordFormInitial`, `RecordFormLoading`, `RecordFormReady(categories, factors)`,
  `RecordFormSubmitting`, `RecordFormSuccess(record)`, `RecordFormFailure(fieldErrors)`.
- Live preview uses `quantity × factor` on the client only for hint; the saved value comes from the
  backend response.

## Backend logic

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/v1/records` | JWT | list/search/filter own records |
| POST | `/api/v1/records` | JWT | create + calculate |
| GET | `/api/v1/records/{id}` | JWT | detail + formula |
| PATCH | `/api/v1/records/{id}` | JWT | edit quantity/date/notes/factor |
| DELETE | `/api/v1/records/{id}` | JWT | soft delete |
| GET | `/api/v1/records/{id}/calculation` | JWT | formula breakdown |

Rules:
- Ownership: `user_id` must match; organization records also check `organization_id`.
- Quantity > 0; date not in the future (allow today); unit must equal factor unit; factor active.
- Snapshot `factor_grams_co2e`, source/year text, and unit.
- `emissions_grams = round(quantity × factor_grams_co2e)`; display kg = grams / 1000, 2 decimals.
- Edit recalculates using the original snapshot unless the factor is explicitly changed.
- Soft delete (`status=deleted`) keeps history; reports exclude deleted.
- A document-linked record is created only through document confirmation (feature 04).

## Data

Table: `consumption_records`.
Invariants: emissions integer grams; factor snapshot; user/org ownership; activity date; status;
source; optional one-to-one document.

## Acceptance criteria

1. A user can create a record for each of the seven categories.
2. The server rejects zero/negative quantity, missing factor, mismatched unit, inactive factor,
   future date, and foreign category.
3. The response includes `emissions_grams`, `emissions_kg`, the snapshot, and a formula string.
4. Editing quantity recalculates and updates the dashboard/report.
5. Deleting soft-deletes and removes the record from lists/reports.
6. A user cannot read/edit/delete another user’s record.
7. The record detail shows the factor source and year.
8. Empty/loading/error states render in EN and AR.

## Tests

| Type | File | Covers |
|---|---|---|
| Unit | `tests/modules/records/test_calculation.py` | rounding, units, snapshots, zero/negative |
| Service | `tests/modules/records/test_services.py` | ownership, edit, soft delete |
| API | `tests/api/test_records.py` | CRUD, validation, auth, org scope |
| Mobile BLoC | `test/features/records/records_bloc_test.dart` | list/empty/failure, form submit |
| Widget | `test/features/records/record_form_page_test.dart` | validation/live preview/EN-AR |

## Status

🟡 in progress — issue #7.

Related: #7
