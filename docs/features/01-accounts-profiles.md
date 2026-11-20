# 01 — Accounts, profiles & preferences

## Purpose

Let guests understand the product and register, and let users maintain the identity, account type,
household/organization details, locale, timezone, and privacy preferences that every other feature
depends on.

## UI (Flutter)

| Screen | Elements |
|---|---|
| `WelcomePage` | hero image, value props, language switch, login/register, content preview |
| `LoginPage` | email/password, show/hide, submit, validation, error, loading |
| `RegisterPage` | name/email/password, account type segmented control, organization fields when needed, locale/timezone, terms, validation |
| `ProfilePage` | avatar (optional), name/email read-only, phone, country/city, household size/home type, locale, timezone, leaderboard opt-in + alias |
| `OrganizationPage` | name (EN/AR), type, industry, country/city, size, contact email |
| `SettingsPage` | language, default period, notification preferences link, logout, app version |
| `GuestContentPage` | published articles, register prompt |

States: loading, empty (no articles), success, validation error, network error, submitting,
unauthorized, account suspended.

## Screen logic (BLoC)

`AuthBloc`
- Events: `AuthStarted`, `AuthLoginSubmitted`, `AuthRegisterSubmitted`, `AuthLogoutRequested`,
  `AuthSessionExpired`.
- States: `AuthInitial`, `AuthLoading`, `AuthAuthenticated(User)`, `AuthUnauthenticated`,
  `AuthFailure(message, fieldErrors)`.
- On success: save tokens in secure storage, load `/auth/me`, route to `/home`.
- On 401 refresh failure: clear tokens, route to `/login`.

`ProfileBloc`
- Events: `ProfileStarted`, `ProfileSaved`, `OrganizationSaved`, `LocaleChanged`,
  `LeaderboardOptInChanged`.
- States: `ProfileInitial`, `ProfileLoading`, `ProfileSuccess(Profile)`, `ProfileSaving`,
  `ProfileFailure`.
- Locale changes update `MaterialApp.locale` and persist; RTL is applied immediately.

## Backend logic

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/v1/auth/register` | public | create user + organization if needed, return tokens |
| POST | `/api/v1/auth/login` | public | verify password, return tokens |
| POST | `/api/v1/auth/refresh` | refresh | rotate refresh token |
| POST | `/api/v1/auth/logout` | JWT | revoke refresh token |
| GET | `/api/v1/auth/me` | JWT | current user + profile |
| PATCH | `/api/v1/auth/me` | JWT | name/locale/timezone |
| PATCH | `/api/v1/auth/password` | JWT | change password |
| GET/PATCH | `/api/v1/profile` | JWT | profile/household/preferences |
| GET/PATCH | `/api/v1/organization` | JWT (org) | organization profile |

Rules:
- Email unique/lower-case; password hashed; generic login errors.
- Organization account requires `organization_name`; created in the same transaction.
- `user_profiles` created automatically; `leaderboard_opt_in` defaults false.
- Account suspension blocks login and JWT use.
- No self-service email reset in v1; admin can reset.
- Admin UI is English; content fields are bilingual.

## Data

Tables: `users`, `user_profiles`, `organizations`, `refresh_tokens`, `admins` (admin only).
Invariants: one profile per user; organization owner is the user; `organization_id` required for
organization accounts; tokens hashed/revocable.

## Acceptance criteria

1. A guest can browse public content and open login/register.
2. Registering an individual creates a user + profile and returns working tokens.
3. Registering an organization creates the organization, user, and profile atomically.
4. Login with wrong credentials returns `401 invalid_credentials` without account enumeration.
5. Access token refresh rotates the refresh token and rejects the old one.
6. Logout revokes the refresh token and clears secure storage.
7. A suspended user cannot log in or use a valid access token.
8. Locale change persists and switches the app between EN and AR/RTL.
9. Leaderboard opt-in is off by default; enabling it requires an alias.
10. Profile validation errors are shown inline and server-side.

## Tests

| Type | File | Covers |
|---|---|---|
| Service | `tests/modules/auth/test_services.py` | register/login/refresh/revoke, org creation |
| API | `tests/api/test_auth.py` | status/shapes/validation/ownership |
| API | `tests/api/test_profile.py` | profile/org updates, leaderboard privacy |
| Mobile BLoC | `test/features/auth/auth_bloc_test.dart` | success/failure/logout sequences |
| Widget | `test/features/auth/login_page_test.dart` | loading/error/validation, EN/AR |

## Status

🟡 in progress — issue #5 (implementation), docs complete.

Related: #5
