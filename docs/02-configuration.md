# 02 — Configuration

All values come from `backend/.env` (never committed). `.env.example` is committed with empty
secret values.

| Key | Default | Meaning |
|---|---|---|
| `FLASK_ENV` | `development` | environment name |
| `SECRET_KEY` | — (required) | Flask session signing; change per install |
| `JWT_SECRET_KEY` | — (required) | JWT signing; change per install |
| `JWT_ACCESS_MINUTES` | `30` | access token lifetime |
| `JWT_REFRESH_DAYS` | `30` | refresh token lifetime |
| `DATABASE_URL` | `sqlite:///instance/carbonwise.sqlite3` | **SQLite only**; relative to `backend/` |
| `HOST` | `127.0.0.1` | bind address |
| `PORT` | `5000` | API/admin port |
| `DEFAULT_LANGUAGE` | `ar` | fallback app locale (device EN/AR is preferred) |
| `CURRENCY` | `N/A` | no commerce; kept for template compatibility |
| `OPENROUTER_API_KEY` | empty | backend only; AI disabled until set |
| `OPENROUTER_MODEL` | `openrouter/free` | fixed; startup guard rejects anything else |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | provider endpoint |
| `AI_DAILY_TOKEN_BUDGET` | `200000` | global per-day cap |
| `AI_RATE_LIMIT_PER_HOUR` | `20` | per-user cap |
| `AI_CACHE_TTL_MINUTES` | `60` | prompt-hash cache TTL |
| `AI_MAX_RETRIES` | `2` | bounded retries on 429/5xx |
| `AI_REQUEST_TIMEOUT_SECONDS` | `45` | HTTP timeout |
| `AI_COMPLETION_TOKEN_FLOOR` | `4096` | minimum completion budget |
| `AI_REASONING_TOKEN_CAP` | `1024` | caps hidden reasoning |
| `UPLOAD_FOLDER` | `instance/uploads` | private upload storage, not public static |
| `MAX_CONTENT_LENGTH` | `31457280` | 30 MB request cap |
| `MAX_IMAGE_BYTES` | `10485760` | 10 MB per image/PDF |
| `ALLOWED_IMAGE_TYPES` | `image/jpeg,image/png,image/webp` | validated by content |
| `ALLOWED_DOCUMENT_TYPES` | `application/pdf` | PDF attachments, no AI extraction |
| `ADMIN_SEED_EMAIL` | `admin@carbonwise.demo` | seed super admin |
| `ADMIN_SEED_PASSWORD` | empty | seed only; set locally, never commit |
| `DEMO_SEED_DATE` | `2026-06-30` | fixed end of the six-month demo window |
| `SIGNIFICANT_INCREASE_PERCENT` | `20` | alert threshold vs previous period |
| `SIGNIFICANT_INCREASE_MIN_KG` | `10` | minimum emissions before alerting |
| `AI_SCREENSHOT_MODE` | `0` | local-only admin screenshot auto-login; never production |

## Emission factor sources

The seed contains illustrative v1 factors. Each factor row stores a source name, source year,
region, validity date, and (where available) a source URL, and every record snapshots the
factor value and source text at write time.

| Category | Seeded factor examples | Primary source |
|---|---|---|
| Electricity | grid electricity 233 g/kWh; natural gas 2,020 g/m³ | DEFRA/BEIS 2025 |
| Transport | petrol car 170 g/km; diesel 171; hybrid 90; bus 82; rail 35 g/passenger-km | DEFRA/BEIS 2025 |
| Flights | short-haul 255; long-haul 150 g/passenger-km | DEFRA/BEIS 2025 |
| Water | supply 344; wastewater 272 g/m³ | UK Water Industry 2024 |
| Waste | landfill 586; recycling 21 g/kg | DEFRA/BEIS 2025 |
| Food | beef 60,000; chicken 6,900; vegetables 2,000; dairy 3,200 g/kg | Poore & Nemecek / Our World in Data (2018) |
| Shopping | clothing 15,000 g/item; electronics 50,000 g/item; parcel 500 g/package | WRAP / DEFRA 2024; manufacturer LCA ranges |

**Method:** activity quantity × factor (grams CO2e per unit), rounded half-up to an integer
number of grams. The factor value and source text are written into the record, so later
catalog edits never rewrite history. EPA and IPCC guidance informed the general inventory and
CO2e methodology; the seeded numeric values above are the demo's cited sources, not a claim of
EPA/IPCC certification. This is a teaching/demo dataset, not an audited carbon inventory.

## Rules

- `DATABASE_URL` must start with `sqlite:`; the app refuses to boot otherwise.
- `OPENROUTER_MODEL` must be exactly `openrouter/free`; no fallback, no paid model.
- Secrets never appear in docs, logs, tests, or the mobile app.
- `TestingConfig` blanks the AI key so tests never call the provider.
- `AI_SCREENSHOT_MODE` is only for local screenshot generation; it must be off by default and
  documented as unsafe outside a local demo.
- Uploads are private under `backend/instance/uploads/`; no cloud storage.
- The seed is deterministic and uses `DEMO_SEED_DATE` for its fixed window.

Related: #2, #5, #15
