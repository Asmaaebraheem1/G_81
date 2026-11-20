# Demo — CarbonWise

## Before you start

| Item | Value |
|---|---|
| Backend | `http://127.0.0.1:5000` |
| API health | `http://127.0.0.1:5000/api/v1/health` |
| Swagger | `http://127.0.0.1:5000/api/` |
| Admin | `http://127.0.0.1:5000/admin/login` |
| Admin login | `admin@carbonwise.demo` / `Admin123!` |
| Content editor | `editor@carbonwise.demo` / `Editor123!` |
| Demo user (EN, individual) | `sara@carbonwise.demo` / `User123!` |
| Demo user (AR, household) | `ahmad@carbonwise.demo` / `User123!` |
| Demo organization | `org@carbonwise.demo` / `Org123!` |
| Mobile | Android emulator → `http://10.0.2.2:5000/api/v1` |
| Reset | `python -m flask --app run.py seed --reset` |

These are **demo credentials only**. Never reuse them for a real deployment. The seed is
deterministic and uses a fixed six-month window ending `2026-06-30`.

## 10-minute path

| # | Step | Expected |
|---|---|---|
| 1 | Open admin, log in as `admin@carbonwise.demo` | dashboard KPIs: users, records, total kg CO2e, goals, plans, AI calls |
| 2 | Open Users, search “Sara” | seeded user row; open detail; records/goals/plans visible |
| 3 | Open Emission Factors | 20 seeded factors with source, unit, region, validity |
| 4 | Open Consumption Records → a record | quantity, factor snapshot, formula, emissions |
| 5 | Open AI Monitoring | usage rows, models, failures, flagged responses; no raw prompts |
| 6 | Open Content, edit/publish an article | bilingual fields saved; app reflects it |
| 7 | Open mobile app, switch EN/AR | RTL layout, persisted locale |
| 8 | Log in as `sara@...`, open dashboard | total, category chart, recent records |
| 9 | Add an electricity record | preview formula → save → dashboard total updates |
| 10 | Upload a bill image | consent → extraction (if vision available) → confirm → record created |
| 11 | Open Reports → set period → export CSV | charts, comparison, top activities, CSV download |
| 12 | Create a goal (e.g., −15% this month) | baseline/target/progress shown |
| 13 | Generate a reduction plan | structured actions, priorities, timeline, calculated savings |
| 14 | Ask the AI assistant “Why did my emissions change?” | grounded answer with calculated context; report/flag action |
| 15 | Join a challenge, mark a plan action complete | points/badge notification; admin sees the activity |

## Fallbacks

- **AI disabled / no key:** show “AI is not configured” and the calculated/rules fallback; demo
  the reports and template plan.
- **AI 429 / outage:** show the friendly retry message; retry once with backoff; use the fallback.
- **Vision unavailable:** show `vision_unavailable` and the manual-entry form; the uploaded file
  remains attached.
- **Empty DB:** `python -m flask --app run.py seed --reset`, then retry.
- **Offline mobile:** show cached data + offline banner; writes queue is out of scope.
- **Emulator cannot reach backend:** check `10.0.2.2`, `HOST=0.0.0.0`, and Windows Firewall.
- **Arabic layout issue:** switch to EN, show the same screen, note the fix in the review.

## Reset after the demo

```cmd
cd backend
.venv\Scripts\activate
python -m flask --app run.py seed --reset
```

## Seed content checklist

- 7 categories, 20 factors, 12 alternatives.
- 3 users + 1 organization + 2 admins.
- 60 records, 3 documents, 4 goals, 3 plans, 5 challenges, 12 badges, 20 points entries.
- 8 notifications, 8 articles, 10 AI usage rows, 10 audit entries.

Related: #19, #20
