# ADR-0005 — JWT for the API, cookie sessions for the admin

- **Status:** accepted
- **Date:** 2026-11-19
- **Deciders:** owner + agent

## Context

The Flutter app needs stateless mobile auth; the server-rendered Jinja admin needs browser
sessions and CSRF. Mixing them creates CSRF and token-leak risks.

## Decision

- `/api/v1` uses JWT access + refresh (`Flask-JWT-Extended`), stored in `flutter_secure_storage`.
- `/admin` uses signed-cookie sessions + CSRF (`Flask-WTF`), with `login_required` on every view.
- The API rejects cookies; the admin rejects JWTs.
- Refresh tokens are hashed in SQLite and rotated/revoked.

## Consequences

### Positive
- Mobile-friendly stateless access.
- Browser CSRF protection for admin forms.
- Clear security boundary.

### Negative / trade-offs
- Two auth code paths to test.
- Refresh token rotation needs care.

### Follow-ups
- Add login rate limiting.
- Add admin session expiry and audit logging.

## Alternatives considered

| Alternative | Why not |
|---|---|
| JWT for admin | Token storage/CSRF risk in a browser |
| Cookies for the API | CSRF risk; poor mobile fit |
| OAuth provider | Out of scope, external dependency |

Related: #5, #15
