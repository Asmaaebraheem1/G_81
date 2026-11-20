# Mobile — navigation (go_router)

## What it is

`go_router` defines the app routes, auth redirects, the main shell, and deep links.

## Why it exists

The app has public (welcome/login/register/content) and authenticated (dashboard, records,
reports, goals, plans, AI, challenges, settings) areas. A single redirect rule prevents
unauthenticated access and sends logged-in users away from auth screens.

## Route map

| Path | Screen | Auth |
|---|---|---|
| `/` | welcome | public |
| `/login` | login | public |
| `/register` | register | public |
| `/home` | dashboard | JWT |
| `/records` | records | JWT |
| `/records/new` | add record | JWT |
| `/records/:id` | record detail | JWT |
| `/documents` | documents | JWT |
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
| `/achievements` | achievements | JWT |
| `/leaderboard` | leaderboard | JWT |
| `/notifications` | notifications | JWT |
| `/settings` | settings | JWT |
| `/organization` | organization | JWT org |
| `/content` | articles | public |
| `/content/:slug` | article detail | public |

## Shell

`AppShell` provides bottom navigation for Home, Records, Reports, AI, and More. The “More” sheet
links Goals, Plans, Alternatives, Challenges, Achievements, Leaderboard, Notifications, Settings,
Organization, and Content.

## Redirect rules

- Not authenticated + private route → `/login?from=<path>`.
- Authenticated + `/login` or `/register` → `/home`.
- Organization route + non-organization account → `/home` with a message.
- Unknown route → `/` (or a not-found page).

## Deep links

Notification `action_url` values use app paths (e.g. `/goals/3`). The router handles them after
auth. Do not put tokens in URLs.

## Testing

Widget tests pump `MaterialApp.router` with a fake auth state and assert redirects/route
rendering. No real navigation stack leaks between tests.

## Related

- Pages: [app architecture](app-architecture.md), [BLoC](bloc.md)
