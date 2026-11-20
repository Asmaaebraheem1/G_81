# 13 — Admin core, users & organizations

## Purpose

Provide the back-office shell: secure cookie login, dashboard KPIs, user and organization
management, admin roles/settings, and an audit trail.

## UI (Jinja2)

| Page | Elements |
|---|---|
| `/admin/login` | email/password, CSRF, error, loading |
| `/admin/` | KPI cards, category chart, recent records/users, AI calls, quick links |
| `/admin/users` | search, filters (type/status), table, pagination, empty/loading/error |
| `/admin/users/{id}` | profile, account type, organization, records summary, goals/plans, actions |
| `/admin/organizations` | search, table, status |
| `/admin/organizations/{id}` | profile, owner, records summary, sustainability totals |
| `/admin/settings` | admin profile, password, roles, platform settings |
| `/admin/admins` | admin accounts/roles (super admin only) |
| `/admin/audit` | audit log with filters |

States: login error, CSRF error, empty tables, no permission, confirmation dialogs, success flash,
validation errors, 404.

## Screen logic

- Session login → `login_required` on every page.
- Role decorator: `super_admin` all; `content_editor` content/challenges only, read-only elsewhere.
- Forms use Flask-WTF CSRF; validation errors re-render with messages.
- Destructive actions require a confirmation dialog and write an audit log.
- Search/filter/sort/pagination are server-side.
- All changes flash a success message.

## Backend logic

| Route | Methods | Role | Purpose |
|---|---|---|---|
| `/admin/login` | GET/POST | public | session login |
| `/admin/logout` | GET | logged-in | logout |
| `/admin/` | GET | logged-in | dashboard |
| `/admin/users` | GET | logged-in | list/search |
| `/admin/users/{id}` | GET | logged-in | detail |
| `/admin/users/{id}/status` | POST | super_admin | activate/suspend |
| `/admin/users/{id}/reset-password` | POST | super_admin | reset |
| `/admin/organizations` | GET | logged-in | list |
| `/admin/organizations/{id}` | GET | logged-in | detail |
| `/admin/organizations/{id}/status` | POST | super_admin | verify/suspend |
| `/admin/settings` | GET/POST | logged-in | profile/platform settings |
| `/admin/admins` | GET/POST | super_admin | admin CRUD/roles |
| `/admin/audit` | GET | super_admin | audit log |

Rules:
- Passwords hashed; generic login errors; rate limit.
- Cannot deactivate the last active super admin.
- Audit: user status/reset, org status, admin changes, settings.
- CSRF on every POST; autoescaping on.

## Data

Tables: `admins`, `users`, `user_profiles`, `organizations`, `admin_audit_logs`, `app_settings`.
Invariants: role enum, last-super-admin guard, soft status, audit append-only.

## Acceptance criteria

1. Admin login requires a valid password and rejects invalid/CSRF requests.
2. Every admin page requires login; content editor is blocked from super-admin pages.
3. Dashboard KPIs match the database counts/totals.
4. User search/filter/pagination works; detail shows related records.
5. User activate/suspend and password reset work and are audited.
6. Organization verify/suspend works and is audited.
7. The last active super admin cannot be deactivated.
8. Settings persist and are audited.
9. Empty/error/permission states render cleanly.
10. No JWT is accepted by admin routes.

## Tests

| Type | File | Covers |
|---|---|---|
| Service | `tests/modules/admin/test_services.py` | roles, last-super-admin, audit |
| Admin | `tests/admin/test_auth.py` | login, CSRF, login_required |
| Admin | `tests/admin/test_users.py` | search/status/reset/permissions |
| Admin | `tests/admin/test_organizations.py` | list/detail/status |
| Admin | `tests/admin/test_dashboard.py` | KPI counts |

## Status

🟡 in progress — issue #15.

Related: #15
