# Mobile — BLoC

## What it is

`flutter_bloc` is the only state-management library. Each feature exposes a BLoC with explicit
events and freezed states.

## Why it exists

Events make user actions testable; explicit states make loading/empty/success/failure UI
predictable and screenshot-friendly.

## Pattern

```dart
sealed class RecordsEvent {}
final class RecordsStarted extends RecordsEvent {}
final class RecordsFilterChanged extends RecordsEvent { ... }

@freezed
sealed class RecordsState with _$RecordsState {
  const factory RecordsState.initial() = _Initial;
  const factory RecordsState.loading() = _Loading;
  const factory RecordsState.empty() = _Empty;
  const factory RecordsState.success(List<RecordEntity> records) = _Success;
  const factory RecordsState.failure(String message) = _Failure;
}
```

- One BLoC per screen concern; shared data uses repositories/cubits.
- No `setState` for business state.
- UI only emits events and renders states.
- Errors are mapped to friendly, localized messages.
- On success, invalidate dependent caches (dashboard/report) via a shared `RefreshBus` or by
  re-fetching on screen focus.

## State rules

- Every state list has `initial`, `loading`, `empty` (where applicable), `success`, `failure`.
- Forms have `submitting`, `validationError`, `submitSuccess`, `submitFailure`.
- AI features have `disabled`, `loading`, `success`, `rateLimited`, `visionUnavailable`, `failure`.
- No `pumpAndSettle()` in tests when a spinner may run; use explicit `pump()`.

## Testing

`bloc_test` asserts the exact state sequence for success, empty, and failure. Repositories are
faked with `mocktail`. See `docs/testing/strategy.md`.

## Related

- Pages: [app architecture](app-architecture.md), [testing](../testing/strategy.md)
