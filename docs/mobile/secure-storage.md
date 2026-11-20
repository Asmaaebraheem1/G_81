# Mobile — secure storage and token lifecycle

## What it is

`flutter_secure_storage` stores the JWT access and refresh tokens only. It is never used for
general preferences or cached data.

## Why it exists

Tokens must not appear in sqflite, `shared_preferences`, logs, crash reports, or screenshots.
Android Keystore/EncryptedSharedPreferences provides OS-backed protection.

## Lifecycle

1. Login/register response → save access + refresh.
2. Dio interceptor attaches the access token.
3. On `401 token_expired` → call `/auth/refresh` once with the refresh token.
4. Save the rotated pair; retry the original request.
5. Refresh failure → clear tokens, emit logged-out, route to `/login`.
6. Logout → call `/auth/logout`, clear tokens, clear user-scoped cache, route to `/`.

## Rules

- Keys: `access_token`, `refresh_token` (no other secrets).
- No token in URLs, query strings, logs, analytics, or screenshots.
- Do not store passwords.
- Clear tokens on 401 refresh failure and on account suspension.
- Locale preference may use secure storage or the local settings table; tokens take priority.
- Tests use a fake token store; never the real Keystore.

## Testing

Unit tests assert save/read/clear and refresh-once. Widget tests assert the router redirects after
logout. No real secure storage in tests.

## Related

- ADR-0005
- Pages: [networking](networking.md), [navigation](navigation.md)
