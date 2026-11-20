# Mobile — app architecture

## What it is

A feature-first Flutter app using BLoC, Dio, sqflite, go_router, freezed, and
flutter_secure_storage. Each feature has data/domain/presentation layers.

## Why it exists

The app must stay testable and offline-tolerant while the backend remains authoritative. Feature
folders keep the large scope (records, reports, goals, plans, challenges, AI, admin-facing data)
navigable.

## How it works

```
main.dart
  → AppConfig (API base URL, locale)
  → AppDatabase (sqflite)
  → ApiClient (Dio + auth/refresh)
  → repositories per feature
  → BlocProvider / RepositoryProvider
  → AppRouter (go_router)
  → CarbonWiseApp (MaterialApp.router, EN/AR, RTL)
```

- Dependency injection is manual via `RepositoryProvider`/`BlocProvider`; no service locator.
- `AuthCubit` owns the session state and token lifecycle.
- Feature BLoCs receive repositories through constructors.
- The router uses `redirect` to protect authenticated routes.
- `AppShell` provides bottom navigation for the main areas.

## Layers

| Layer | Contains | Rule |
|---|---|---|
| data | DTOs, Dio datasources, sqflite cache, repository impl | no UI |
| domain | entities, contracts, use cases | no Flutter widgets |
| presentation | BLoC, pages, widgets | no direct Dio/sqflite |

## How to use it

Add a feature:

1. `features/<name>/domain/` — entity + repository contract + use case.
2. `features/<name>/data/` — DTO + remote/local datasource + repository impl.
3. `features/<name>/presentation/` — BLoC + page + widgets.
4. Register the repository/bloc in `app/di.dart`.
5. Add routes and ARB strings.
6. Add unit + widget tests.

## Testing

Use fake repositories and fake API clients. Widget tests pump the page with a BLoC in each state.
No real network/secure storage.

## Related

- Pages: [BLoC](bloc.md), [networking](networking.md), [local database](local-database.md), [navigation](navigation.md)
