# Mobile — local database (sqflite)

## What it is

A single sqflite database used as an offline read cache. The backend is authoritative.

## Why it exists

The app should still show the last dashboard, categories, factors, records, notifications, and
articles when the network is unavailable. Writes always go to the API; there is no offline write
queue in v1.

## How it works

- `AppDatabase` in `core/database/` owns one open path, version, `onCreate`, and `onUpgrade`.
- Tables:

| Table | Version | Purpose |
|---|---|---|
| `cache_categories` | 1 | category catalog |
| `cache_factors` | 1 | factor catalog |
| `cache_records` | 1 | recent records |
| `cache_dashboard` | 1 | last dashboard summary JSON |
| `cache_notifications` | 1 | latest notifications |
| `cache_articles` | 1 | published articles |
| `cache_ai_status` | 1 | AI enabled/model/vision cache |

- Each cache table has `id`, `payload_json`, `fetched_at`.
- Migrations preserve data; no drop-and-recreate.
- Repository implementations read through the cache on network failure and expose
  `fromCache: true` so the UI can show an offline banner.
- No tokens, prompts, or personal secrets in the cache.
- Non-trivial DB work runs off the UI isolate where needed.

## How to use it

```dart
final db = await AppDatabase.instance.database;
await db.insert('cache_categories', {...}, conflictAlgorithm: ConflictAlgorithm.replace);
```

Feature repositories call `LocalCache` methods; widgets never call sqflite.

## Testing

Unit tests use `sqflite_common_ffi` (dev) or a fake cache repository. Widget tests use fake
repositories; no real database required.

## Related

- Pages: [app architecture](app-architecture.md), [networking](networking.md)
