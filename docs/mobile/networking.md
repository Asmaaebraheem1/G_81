# Mobile — networking (Dio)

## What it is

One configured `Dio` instance (`ApiClient`) with base URL, JSON headers, auth token injection,
refresh-once, timeouts, error mapping, and debug-only logging.

## Why it exists

Centralizing HTTP avoids duplicated interceptors and keeps tokens out of feature code. The refresh
flow must be consistent across every screen.

## How it works

- `API_BASE_URL` comes from `--dart-define`; default `http://10.0.2.2:5000/api/v1`.
- Interceptors:
  1. attach `Authorization: Bearer <access>` except public/auth routes;
  2. on `401 token_expired`, call `/auth/refresh` once, save the new pair, retry the original;
  3. on refresh failure, clear tokens and emit `AuthLoggedOut`;
  4. map Dio errors to `ApiFailure(code, message, status, details)`;
  5. log method/path/status only in debug; never log tokens/body.
- Timeouts: connect 10s, receive 45s (AI can be slower; AI uses a separate longer timeout).
- Multipart upload for documents.
- CSV download for reports uses `ResponseType.bytes`.

## Error mapping

| Condition | App failure |
|---|---|
| No connection | `NetworkFailure` |
| Timeout | `TimeoutFailure` |
| 401 | `UnauthorizedFailure` → logout/refresh |
| 403 | `ForbiddenFailure` |
| 404 | `NotFoundFailure` |
| 422 | `ValidationFailure(details)` |
| 429 | `RateLimitedFailure` |
| 5xx | `ServerFailure` |
| AI disabled/vision unavailable | `AiDisabledFailure` / `VisionUnavailableFailure` |

Raw exceptions never reach widgets.

## Testing

Use a fake `ApiClient`/Dio adapter; assert headers, refresh-once, error mapping, and no token logs.
Widget/BLoC tests use fake repositories, not real HTTP.

## Related

- Pages: [app architecture](app-architecture.md), [secure storage](secure-storage.md)
