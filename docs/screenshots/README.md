# UI screenshot library

All images live flat in `docs/screenshots/` and are named
`<area>-<index>-<screen>.png`. The index keeps files ordered in the same
sequence a reviewer walks the product.

## Naming

| Prefix | Area | Locale |
|---|---|---|
| `mobile-en-` | Flutter app, English | `en` |
| `mobile-ar-` | Flutter app, Arabic + RTL | `ar` |
| `admin-` | Flask/Jinja admin console | English only |

Examples: `mobile-ar-03-dashboard.png`, `mobile-en-21-challenge-detail.png`,
`admin-27-ai-monitor.png`.

## Mobile coverage

| # | Screen / state | EN | AR |
|---|---|---|---|
| 01 | Welcome / guest entry | `mobile-en-01-welcome.png` | gap (captured live only) |
| 02 | Login | `mobile-en-02-login.png` | `mobile-ar-02-login.png` |
| 03 | Home dashboard, success + rules-based AI summary | `mobile-en-03-dashboard.png` | `mobile-ar-03-dashboard.png` |
| 04 | Records list | `mobile-en-04-records.png` | `mobile-ar-04-records.png` |
| 05 | Record detail with factor formula | `mobile-en-05-record-detail.png` | `mobile-ar-05-record-detail.png` |
| 06 | Record form, edit + live calculation | `mobile-en-06-record-form.png` | `mobile-ar-06-record-form.png` |
| 07 | Reports, period + category breakdown | `mobile-en-07-reports.png` | `mobile-ar-07-reports.png` |
| 08 | Assistant, suggested prompts | `mobile-en-08-assistant.png` | `mobile-ar-08-assistant.png` |
| 09 | More / navigation hub | `mobile-en-09-more.png` | `mobile-ar-09-more.png` |
| 10 | Goals list | `mobile-en-10-goals.png` | `mobile-ar-10-goals.png` |
| 11 | Reduction plans list | `mobile-en-11-plans.png` | `mobile-ar-11-plans.png` |
| 12 | Plan detail + backend assumptions | `mobile-en-12-plan-detail.png` | `mobile-ar-12-plan-detail.png` |
| 13 | Notifications | `mobile-en-13-notifications.png` | `mobile-ar-13-notifications.png` |
| 14 | Alternatives | `mobile-en-14-alternatives.png` | `mobile-ar-14-alternatives.png` |
| 15 | Challenges list + filters | `mobile-en-15-challenges.png` | `mobile-ar-15-challenges.png` |
| 16 | Documents + extraction status | `mobile-en-16-documents.png` | `mobile-ar-16-documents.png` |
| 17 | Settings + language switch | `mobile-en-17-settings.png` | `mobile-ar-17-settings.png` |
| 18 | Insights / AI opportunity list | `mobile-en-18-insights.png` | `mobile-ar-27-insights.png` |
| 19 | Assistant chat, backend-number fallback | `mobile-en-19-assistant-chat.png` | `mobile-ar-08-assistant.png` |
| 20 | Goal detail, 100% state | `mobile-en-20-goal-detail.png` | `mobile-ar-18-goal-detail.png` |
| 21 | Challenge detail, completed | `mobile-en-21-challenge-detail.png` | `mobile-ar-19-challenge-detail.png` |
| 22 | Achievements / badges | `mobile-en-22-achievements.png` | `mobile-ar-21-achievements.png` |
| 23 | Leaderboard, opted in | `mobile-en-23-leaderboard.png` | `mobile-ar-20-leaderboard.png` |
| 24 | Learn / article list | `mobile-en-24-learn.png` | `mobile-ar-22-learn.png` |
| 25 | Article detail | `mobile-en-25-article.png` | `mobile-ar-23-article.png` |
| 26 | Organization profile (org user) | `mobile-en-26-organization.png` | `mobile-ar-26-organization.png` |
| 27 | Register (EN) / change-password dialog (AR) | `mobile-en-27-register.png` | `mobile-ar-24-change-password-dialog.png` |
| 28 | Logout confirmation | gap | `mobile-ar-25-logout-dialog.png` |

### Known screenshot gaps

These states are implemented and test-covered but were not captured before
the emulator session ended; they are tracked in `docs/issues.md` and will be
regenerated at the next UI freeze:

- Arabic welcome and Arabic register.
- Failure/loading/empty variants for dashboard, records, reports, assistant,
  plans, challenges, documents, notifications.
- Record delete confirmation, challenge join/verification-pending state.
- Admin 403/404/500 pages (route behaviour verified by tests).

## Admin coverage

| # | Page | File |
|---|---|---|
| 01 | Login | `admin-01-login.png` |
| 02 | Dashboard | `admin-02-dashboard.png` |
| 03 | Users list | `admin-03-users.png` |
| 04 | User detail | `admin-04-user-detail.png` |
| 05 | Records list | `admin-05-records.png` |
| 06 | Record detail + formula | `admin-06-record-detail.png` |
| 07 | Reports | `admin-07-reports.png` |
| 08 | Categories | `admin-08-categories.png` |
| 09 | Category form | `admin-09-category-form.png` |
| 10 | Emission factors | `admin-10-factors.png` |
| 11 | Factor form | `admin-11-factor-form.png` |
| 12 | Goals | `admin-12-goals.png` |
| 13 | Goal detail | `admin-13-goal-detail.png` |
| 14 | Plans | `admin-14-plans.png` |
| 15 | Plan detail | `admin-15-plan-detail.png` |
| 16 | Challenges | `admin-16-challenges.png` |
| 17 | Challenge form | `admin-17-challenge-form.png` |
| 18 | Badges | `admin-18-badges.png` |
| 19 | Documents | `admin-19-documents.png` |
| 20 | Document detail | `admin-20-document-detail.png` |
| 21 | Content articles | `admin-21-content.png` |
| 22 | Article form | `admin-22-article-form.png` |
| 23 | Notifications | `admin-23-notifications.png` |
| 24 | Notification form | `admin-24-notification-form.png` |
| 25 | Organizations | `admin-25-organizations.png` |
| 26 | Organization detail | `admin-26-organization-detail.png` |
| 27 | AI monitoring | `admin-27-ai-monitor.png` |
| 28 | Audit log | `admin-28-audit.png` |
| 29 | Settings | `admin-29-settings.png` |

## How images were produced

- **Mobile:** debug APK built with
  `--dart-define=API_BASE_URL=http://10.0.2.2:5001/api/v1`, installed on a
  1080x2400 Pixel AVD, signed in as the seeded demo user. Locale switched in
  **Settings → App language**. No real personal data is shown.
- **Admin:** local Flask app on `127.0.0.1:5001`, Playwright + headless Edge,
  signed in as `admin@carbonwise.demo`; seeded demo data only.
- **Never** capture real emails, access tokens, OpenRouter keys, or uploaded
  bill contents. The demo alias and demo e-mails are fictional.

## Regeneration checklist

1. Start the backend on port 5001 and confirm
   `GET /api/v1/health` returns a `data` envelope.
2. Build/install the debug APK with the emulator base URL above.
3. Capture EN first, then switch to Arabic in Settings and capture AR again.
4. Capture admin pages with `%TEMP%\cw_pw\shots.js` (Playwright).
5. Replace the files in this folder, keep the numbering, and update this
   table in the same pull request as the UI change.

Screenshots are regenerated whenever a UI change alters layout, copy, or
state, and the coverage table is reviewed in the PR checklist.
