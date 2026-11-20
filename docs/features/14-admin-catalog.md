# 14 — Admin catalog, records & documents

## Purpose

Let admins manage the emission catalog (categories/factors), inspect consumption records with their
calculation breakdown, and review/download uploaded documents.

## UI (Jinja2)

| Page | Elements |
|---|---|
| `/admin/categories` | table, create/edit form, bilingual names, order, active, delete/deactivate |
| `/admin/factors` | table, create/edit, category, unit, factor grams, source/URL/year, region, validity, active |
| `/admin/records` | search/filter (user, category, date, status), table, pagination |
| `/admin/records/{id}` | quantity, factor snapshot, formula, emissions, user/org, attachment, flag/soft-delete |
| `/admin/documents` | table, status, user, size/MIME, extraction model, download, delete |
| `/admin/documents/{id}` | metadata, extraction JSON, linked record, authenticated download |

States: empty, loading (table skeleton), success, validation error, confirmation, 404, no
permission, filter no results.

## Screen logic

- Server-side forms with CSRF; validation errors inline.
- Category/factor deactivate rather than delete when referenced.
- Factor changes do not rewrite historical records (snapshots).
- Record flag/soft-delete requires confirmation + audit.
- Document download is authenticated and audited.
- Content editor: read-only for these pages.

## Backend logic

| Route | Methods | Purpose |
|---|---|---|
| `/admin/categories` | GET/POST | list/create |
| `/admin/categories/{id}` | GET/POST | edit/deactivate |
| `/admin/factors` | GET/POST | list/create |
| `/admin/factors/{id}` | GET/POST | edit/deactivate |
| `/admin/records` | GET | search/filter |
| `/admin/records/{id}` | GET | detail/formula |
| `/admin/records/{id}/flag` | POST | flag |
| `/admin/records/{id}/delete` | POST | soft delete |
| `/admin/documents` | GET | list |
| `/admin/documents/{id}` | GET | detail |
| `/admin/documents/{id}/download` | GET | authenticated file |
| `/admin/documents/{id}/delete` | POST | delete if unlinked |

Rules:
- Factor value positive integer; unit/category required; source/region/validity required.
- Deactivating does not affect existing records.
- Document deletion checks `record_id`; linked documents cannot be deleted.
- Audit: category/factor changes, record flag/delete, document delete.
- No direct filesystem path exposure.

## Data

Tables: `emission_categories`, `emission_factors`, `consumption_records`, `documents`,
`admin_audit_logs`.

## Acceptance criteria

1. Admin can create/edit/deactivate categories with EN/AR names.
2. Admin can create/edit/deactivate factors with source/unit/region/validity.
3. Factor validation rejects invalid values/URLs/dates.
4. Historical records keep their snapshots after factor edits.
5. Record search/filter/pagination works and shows the formula.
6. Flag/soft-delete works and is audited.
7. Documents list/detail/download works; linked documents cannot be deleted.
8. Content editor sees read-only pages.
9. Empty/error/confirmation states render cleanly.

## Tests

| Type | File | Covers |
|---|---|---|
| Service | `tests/modules/catalog/test_admin.py` | CRUD/validation/deactivate |
| Admin | `tests/admin/test_catalog.py` | list/create/edit/CSRF |
| Admin | `tests/admin/test_records.py` | search/formula/flag/delete |
| Admin | `tests/admin/test_documents.py` | list/download/delete guard |

## Status

🟡 in progress — issue #16.

Related: #16
