# Backend — authentication

## What it is

Two separate auth surfaces:

| Surface | Mechanism | Storage |
|---|---|---|
| `/api/v1` | JWT access + refresh (`Flask-JWT-Extended`) | mobile `flutter_secure_storage` |
| `/admin` | signed-cookie session + CSRF (`Flask-WTF`) | browser cookie |

## Why it exists

The mobile app needs stateless tokens; the Jinja admin needs CSRF-protected browser sessions.
Mixing them creates CSRF and token-leak risks. See ADR-0005.

## API auth flow

1. `POST /auth/register` or `/auth/login` → access + refresh tokens.
2. App stores tokens in `flutter_secure_storage`.
3. Dio attaches `Authorization: Bearer <access>`.
4. On `401`, the interceptor calls `/auth/refresh` once with the refresh token, retries the
   original request, and logs out on failure.
5. `POST /auth/logout` revokes the refresh token row.

Refresh tokens are hashed (`sha256`) in `refresh_tokens`; raw tokens are never stored. Access
tokens are short-lived (~30 min); refresh tokens expire after ~30 days and rotate.

## Admin auth flow

1. `GET /admin/login` renders a CSRF-protected form.
2. `POST /admin/login` verifies the password hash and sets a signed session cookie.
3. Every admin view uses `login_required`; every POST form uses CSRF.
4. `GET /admin/logout` clears the session.
5. Roles: `super_admin` (all) and `content_editor` (content/challenges; read-only elsewhere).

## Rules

- Passwords hashed with `werkzeug.security`; never logged.
- Generic login errors; no account enumeration.
- API rejects cookies; admin rejects JWTs.
- Admin reset-password is available; self-service email reset is out of scope.
- Login rate limiting is required.

## Testing

- API: register/login/refresh/logout, wrong password, expired/revoked token, ownership.
- Admin: login required, CSRF failure, role permission.
- No real tokens in test logs.

## Related

- ADR-0005
- Pages: [API](api.md), [admin panel](admin-panel.md)
