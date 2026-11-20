# 05 — Dashboard, reports & export

## Purpose

Turn calculated records into an understandable footprint: totals, category shares, trends,
period comparisons, top activities, goal progress, and an exportable summary.

## UI (Flutter)

| Screen | Elements |
|---|---|
| `HomeDashboardPage` | period selector, total kg CO2e, category donut/bar, trend line, goal progress, recent records, AI insight teaser |
| `ReportsPage` | period picker, summary cards, category breakdown, trend, comparison, top activities, export |
| `CategoryDetailPage` | category total/share, monthly trend, records, factor source, tips |
| `ExportSheet` | date range, CSV download/share, print-friendly summary, errors |

States: loading, empty (no records), success, partial data, error, offline cache, exporting,
export success/failure.

## Screen logic (BLoC)

`DashboardBloc`
- Events: `DashboardStarted`, `DashboardPeriodChanged`, `DashboardRefreshed`.
- States: `DashboardInitial`, `DashboardLoading`, `DashboardEmpty`, `DashboardSuccess(summary)`,
  `DashboardFailure(message)`.

`ReportsBloc`
- Events: `ReportsStarted`, `ReportsPeriodChanged`, `ReportsExportRequested`.
- States: `ReportsLoading`, `ReportsSuccess(report)`, `ReportsFailure`,
  `ReportsExporting`, `ReportsExportReady(file)`, `ReportsExportFailure`.

Charts use `fl_chart`; values come from the API, never computed in the widget.

## Backend logic

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/v1/dashboard/summary?period=` | JWT | home summary |
| GET | `/api/v1/reports/summary?period=` | JWT | report summary |
| GET | `/api/v1/reports/trend?months=6` | JWT | monthly trend |
| GET | `/api/v1/reports/categories?period=` | JWT | category totals/shares |
| GET | `/api/v1/reports/top-activities?period=&limit=` | JWT | top records/categories |
| GET | `/api/v1/reports/comparison?period=` | JWT | current vs previous |
| GET | `/api/v1/reports/export.csv?from=&to=` | JWT | CSV export |

Rules:
- Periods: week/month/year, user timezone; custom `from`/`to`.
- Exclude soft-deleted/flagged records.
- Empty data returns zeros and an `empty` flag, not an error.
- Shares use the period total; percentages rounded for display, grams kept internally.
- Comparison uses the immediately previous equivalent period.
- CSV includes date, category, factor, quantity, unit, emissions grams/kg, source.
- No AI in calculated fields; an optional AI summary is feature 08.

## Data

Computed from `consumption_records`, `emission_categories`, `emission_factors`, `goals`.
No report table; aggregates are derived. Optional cache in the app only.

## Acceptance criteria

1. Dashboard shows total, category breakdown, trend, and recent records for the selected period.
2. Reports show current vs previous period and top activities.
3. Empty data shows a friendly empty state, not zeros-only confusion.
4. CSV export respects the date range and ownership and includes the formula fields.
5. Numbers match the record calculation exactly (grams → kg rounding).
6. Period boundaries respect the user timezone.
7. Offline mode shows cached data with an offline banner.
8. EN/AR labels, RTL charts, and number formatting are correct.
9. Export errors are typed and retryable.

## Tests

| Type | File | Covers |
|---|---|---|
| Service | `tests/modules/reports/test_services.py` | aggregation, periods, comparisons, CSV |
| API | `tests/api/test_reports.py` | shapes, auth, empty, export |
| Mobile BLoC | `test/features/reports/reports_bloc_test.dart` | success/empty/failure/export |
| Widget | `test/features/reports/reports_page_test.dart` | charts, EN/AR, empty state |

## Status

🟡 in progress — issue #9.

Related: #9
