# Issue template (fill every section — delete nothing without reason)

## Title
`<type>(<scope>): <short imperative summary>`
e.g. `feat(auth): login screen with JWT`

## Context / Why
What problem exists today? Who is affected? Link the owner's request or related issue.

## Goal
One or two sentences describing the outcome when this issue is done.

## Scope
- Layer(s): backend / mobile / docs / both
- Modules/paths affected: `backend/app/modules/<x>`, `mobile/lib/features/<y>`

## Acceptance criteria (testable, numbered)
1. ...
2. ...
Each criterion must be checkable by a test or an explicit manual step.

## Tasks
- [ ] Design / plan
- [ ] Backend: models, migrations, services, repositories
- [ ] Backend: API endpoints + pydantic schemas + OpenAPI docs
- [ ] Backend: Jinja admin views (if applicable)
- [ ] Mobile: data / domain / presentation layers + BLoC + states
- [ ] Mobile: local SQLite schema/version bump (if applicable)
- [ ] Tests: unit / integration / API / widget / e2e as applicable
- [ ] Docs: `docs/...` pages updated
- [ ] Review

## Test plan
- Automated: which test files will prove each acceptance criterion
- Manual: exact steps (cmd syntax), expected result
- Coverage impact: expected % after this issue (must stay ≥ 50%)

## Out of scope
What this issue deliberately does not do (prevents scope creep).

## Documentation to update
Exact `docs/` files that this change makes stale.

## References
- Branch: `dev/<n>-<slug>`
- PR: (filled when opened)
- Part of: #<epic> (if any)
- Related issues / links / screenshots
