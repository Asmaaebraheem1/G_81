# Glossary

Domain and project terms used in this repo. Keep it short and exact.

| Term | Meaning |
|---|---|
| ARB | Flutter localization resource file (`app_en.arb`, `app_ar.arb`) |
| BLoC | Business Logic Component; events in, states out |
| CO2e | Carbon dioxide equivalent; all emissions are estimated in grams internally, kg in UI |
| Emission factor | Documented grams of CO2e per unit of activity (kWh, m³, L, km, kg) |
| Factor snapshot | The factor value/source/year copied onto a record at calculation time |
| Activity | A user consumption entry (electricity, fuel, transport, flight, water, waste, etc.) |
| Baseline | The comparison period used to calculate a goal’s target |
| Goal | A percentage reduction target over a weekly/monthly/yearly period |
| Plan | A structured set of reduction actions, optionally linked to a goal |
| Alternative | A curated lower-emission option with a documented estimated reduction |
| Challenge | A time-bound sustainability task with progress, points, and optionally a badge |
| Verified action | A challenge action checked by system data or self-report + admin review |
| AI context | The server-built JSON of calculated values sent to the model; never raw database access |
| Best-effort vision | Image extraction only when the routed free model supports images; manual fallback |
| `openrouter/free` | OpenRouter’s free model router; the only allowed AI model |
| JWT | JSON Web Token; access + refresh for the API |
| RTL | Right-to-left layout for Arabic |
| Seed | Deterministic demo data created by `flask seed` |
| ADR | Architecture Decision Record in `docs/decisions/` |
| Hardening | Coverage, lint, EN/AR audit, demo, screenshots, diagrams, handover |
| Local demo | Windows cmd, `127.0.0.1:5000`, Android emulator `10.0.2.2:5000` |
