# Backend — admin panel (Jinja2)

## What it is

A server-rendered back-office at `/admin`, protected by signed-cookie sessions and CSRF. It shares
services with the JSON API but never uses JWT.

## Why it exists

The platform needs centralized management: users, organizations, categories, factors, records,
documents, plans, goals, reports, challenges, notifications, AI monitoring, content, roles, and
settings. A Jinja panel keeps the local demo dependency-free.

## How it works

- `base.html` provides the shell, navigation, flash messages, and CSRF token.
- Each management page has list/search/filter, detail, and forms.
- Forms use `Flask-WTF`; CSRF is mandatory on POST.
- Autoescaping is on; `|safe` is banned.
- Admin actions on sensitive entities call `AdminAuditService.record(...)`.
- Roles are checked in the view or a `role_required` decorator.
- Admin UI is English in v1; content forms edit `*_en` and `*_ar`.

## Pages

| Route | Purpose |
|---|---|
| `/admin/login` | login |
| `/admin/` | KPIs and recent activity |
| `/admin/users` | search/view/activate/suspend/reset password |
| `/admin/organizations` | search/view/verify/suspend |
| `/admin/categories` | CRUD, bilingual names, order |
| `/admin/factors` | CRUD, source/unit/region/validity |
| `/admin/records` | search, formula breakdown, soft delete |
| `/admin/documents` | metadata, authenticated download, delete |
| `/admin/plans` | list/detail/actions |
| `/admin/goals` | list/progress |
| `/admin/reports` | aggregates + CSV |
| `/admin/challenges` | CRUD, rules, points |
| `/admin/badges` | CRUD, award rules |
| `/admin/notifications` | announcements + targeting |
| `/admin/ai` | usage, failures, flagged responses |
| `/admin/content` | bilingual articles, publish |
| `/admin/settings` | admin profile, roles, platform settings |
| `/admin/audit` | audit log |

## Security

- Cookie session + CSRF only; no JWT.
- Passwords hashed; login rate limited.
- No file execution; downloads go through an authenticated route.
- AI monitor never shows raw prompts; reported responses are redacted.
- No secrets in templates or logs.

## Testing

Admin tests use the Flask test client with a logged-in session and CSRF token; they assert
login-required, role permissions, form validation, and audit entries.

## Related

- ADR-0005
- Pages: [authentication](authentication.md), [overview](../00-overview.md)
