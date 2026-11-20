# Issues

Index of GitHub issues. Update in the PR that closes each issue.

| # | Title | Area | Milestone | Status |
|---|---|---|---|---|
| 1 | Epic — CarbonWise | all | — | ✅ closed |
| 2 | Delivery PR — CarbonWise v1 | all | — | ✅ merged |
| 3 | Backend scaffold | backend | M0 | ✅ |
| 4 | Mobile scaffold | mobile | M0 | ✅ |
| 5 | Schema, migrations, deterministic seed | backend | M1 | ✅ |
| 6 | Auth, profiles, guest rules | backend + mobile | M2 | ✅ |
| 7 | Emission catalog & factors | backend + mobile + admin | M3 | ✅ |
| 8 | Consumption records & calculation engine | backend + mobile | M3 | ✅ |
| 9 | Document uploads & AI extraction | backend + mobile | M4 | ✅ |
| 10 | Dashboard, reports & export | backend + mobile | M4 | ✅ |
| 11 | Sustainability goals | backend + mobile | M5 | ✅ |
| 12 | AI reduction plans | backend + mobile | M5 | ✅ |
| 13 | Alternatives & recommendations | backend + mobile | M6 | ✅ |
| 14 | Challenges, badges & leaderboard | backend + mobile + admin | M6 | ✅ |
| 15 | Notifications & reminders | backend + mobile + admin | M6 | ✅ |
| 16 | Admin core, users, organizations | admin | M7 | ✅ |
| 17 | Admin catalog, records, documents | admin | M8 | ✅ |
| 18 | Admin programs, content, analytics, AI monitoring | admin | M8 | ✅ |
| 19 | AI assistant, insights, summaries, flags | backend + mobile | M9 | ✅ |
| 20 | Hardening, coverage, EN/AR audit, demo | all | M10 | ✅ |
| 21 | Diagrams, screenshots, visual assets, AI docs | docs | M10 | ✅ |
| 22 | Post-merge closeout: status, issue index, CI evidence | docs | — | ✅ |

Status: ⬜ not started · 🟡 in progress · ✅ merged/closed.

## Epic

Issue #1 is the epic. Its body lists all children and links to the feature pages below.
Children use `Part of #1` in their bodies and were delivered by PR #2 (`Closes #1`).
GitHub shares one number sequence between issues and pull requests, so the delivery PR
occupies #2 and the child issues are #3–#21.

## Linking rules

- Branch: `dev/<n>-<slug>`
- PR body: `Closes #<n>` (child: `Part of #<epic>`)
- Issue updated with branch + PR link
- Epic keeps a task list of children

Related: #1
