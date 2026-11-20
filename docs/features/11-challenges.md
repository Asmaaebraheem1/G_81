# 11 — Challenges, achievements & leaderboard

## Purpose

Encourage sustainable habits with time-bound challenges, verified progress, points, badges,
milestones, and an opt-in leaderboard.

## UI (Flutter)

| Screen | Elements |
|---|---|
| `ChallengesPage` | tabs active/upcoming/completed, progress bars, join, points, empty/loading/error |
| `ChallengeDetailPage` | rules, target, dates, verification method, progress, join/complete, evidence |
| `AchievementsPage` | badges grid, points total, milestones, locked/unlocked |
| `LeaderboardPage` | opt-in prompt, period filter, rank/alias/points, privacy note |

States: loading, empty, success, joined, in progress, completed, failed, self-report pending,
verification error, opt-in required.

## Screen logic (BLoC)

`ChallengesBloc`
- Events: `ChallengesStarted`, `ChallengeJoined`, `ChallengeProgressSubmitted`,
  `ChallengeRefreshed`.
- States: `ChallengesInitial`, `ChallengesLoading`, `ChallengesEmpty`,
  `ChallengesSuccess(list)`, `ChallengesSubmitting`, `ChallengesFailure`.

`AchievementsBloc` loads badges/points; `LeaderboardBloc` requires opt-in.

## Backend logic

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/v1/challenges` | JWT | active/upcoming/completed |
| GET | `/api/v1/challenges/{id}` | JWT | detail + own progress |
| POST | `/api/v1/challenges/{id}/join` | JWT | join |
| GET | `/api/v1/challenges/{id}/progress` | JWT | progress + verification |
| POST | `/api/v1/challenges/{id}/progress` | JWT | self-report/evidence |
| GET | `/api/v1/achievements` | JWT | badges, points, milestones |
| GET | `/api/v1/leaderboard?period=` | JWT | opt-in ranking |

Rules:
- Verification: system-checked where measurable (record count, reduction % vs baseline, streak,
  completed plan actions); otherwise self-report + optional evidence + admin review. The UI says
  which.
- Joining is idempotent; progress cannot exceed target for completion.
- Completion awards points once (ledger unique reference), badge if configured, notification.
- Leaderboard only includes `leaderboard_opt_in=true` users with aliases; no email/full name.
- No points for AI output; points for actions/records/challenges only.
- Admin CRUD is feature 15.

## Data

Tables: `challenges`, `challenge_participants`, `badges`, `user_badges`, `points_ledger`.
Invariants: one participation per user/challenge; append-only points; badge unique per user;
verification method explicit.

## Acceptance criteria

1. A user can list/join/leave? (join only) and view a challenge.
2. Progress updates according to the verification method.
3. Completion awards points once and a badge when configured.
4. Leaderboard excludes non-opted-in users and personal identifiers.
5. Self-reported actions are labelled and reviewable.
6. Achievements show earned/locked badges and total points.
7. EN/AR and RTL work for all challenge/leaderboard screens.
8. Invalid joins/completions return typed errors.

## Tests

| Type | File | Covers |
|---|---|---|
| Service | `tests/modules/challenges/test_services.py` | join/progress/points/badges/leaderboard |
| API | `tests/api/test_challenges.py` | list/join/progress/achievements/leaderboard |
| Mobile BLoC | `test/features/challenges/challenges_bloc_test.dart` | load/join/progress/failure |
| Widget | `test/features/challenges/challenge_detail_test.dart` | verification label/EN-AR |

## Status

🟡 in progress — issue #13.

Related: #13
