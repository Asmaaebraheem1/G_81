# Mobile — Flutter app

## Structure

```
mobile/lib/
├── main.dart              composition root (DI, runApp)
├── app/                   app widget, router, theme, l10n, shell
├── core/                  config, network (Dio), database (sqflite), error, format
└── features/<feature>/
    ├── data/              dto, remote/local datasource, repository impl
    ├── domain/            entities, repository contract, use cases
    └── presentation/      bloc, pages, widgets
```

## Conventions

- BLoC only; `freezed` states/entities.
- One `ApiClient`; no direct Dio in features.
- One `AppDatabase`; versioned migrations; cache only.
- Tokens in `flutter_secure_storage`; refresh-once interceptor.
- All strings in ARB; EN + AR; RTL tested.
- No business logic in widgets.

## Routes

| Path | Screen | Auth |
|---|---|---|
| `/` | welcome / guest | public |
| `/login` | login | public |
| `/register` | register | public |
| `/home` | dashboard | JWT |
| `/records` | records list | JWT |
| `/records/new` | add record | JWT |
| `/records/:id` | record detail | JWT |
| `/documents` | documents list | JWT |
| `/documents/upload` | upload | JWT |
| `/documents/:id/confirm` | extraction confirmation | JWT |
| `/reports` | reports | JWT |
| `/reports/category/:id` | category detail | JWT |
| `/goals` | goals | JWT |
| `/goals/new` | create goal | JWT |
| `/goals/:id` | goal detail | JWT |
| `/assistant` | AI assistant | JWT |
| `/insights` | AI insights | JWT |
| `/plans` | plans | JWT |
| `/plans/:id` | plan detail | JWT |
| `/alternatives` | alternatives | JWT |
| `/challenges` | challenges | JWT |
| `/challenges/:id` | challenge detail | JWT |
| `/achievements` | badges/points | JWT |
| `/leaderboard` | leaderboard | JWT |
| `/notifications` | notifications | JWT |
| `/settings` | profile/settings | JWT |
| `/organization` | organization profile | JWT org |
| `/content` | articles | public |
| `/content/:slug` | article detail | public |

## Localization setup

`pubspec.yaml` must contain:

```yaml
dependencies:
  flutter_localizations:
    sdk: flutter
  intl: any

flutter:
  generate: true
```

`l10n.yaml`:

```yaml
arb-dir: lib/l10n
template-arb-file: app_en.arb
output-localization-file: app_localizations.dart
```

Files: `lib/l10n/app_en.arb`, `lib/l10n/app_ar.arb`.

## Commands

```cmd
cd mobile
flutter pub get
flutter gen-l10n
flutter analyze
flutter test --coverage
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:5000/api/v1
```

## Base URL

`API_BASE_URL` from `--dart-define`; default `http://10.0.2.2:5000/api/v1` for the emulator.

## Local tables (cache)

| Table | Version | Purpose |
|---|---|---|
| `cache_categories` | v1 | category catalog |
| `cache_factors` | v1 | factor catalog |
| `cache_records` | v1 | recent records |
| `cache_dashboard` | v1 | last dashboard summary |
| `cache_notifications` | v1 | latest notifications |
| `cache_articles` | v1 | published articles |
| `cache_ai_status` | v1 | AI enabled/model/vision capability |

The backend remains authoritative; the cache is read-only for offline display.

Related: #3
