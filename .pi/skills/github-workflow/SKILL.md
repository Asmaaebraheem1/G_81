---
name: github-workflow
description: Branch, issue, and pull-request workflow for this repository. Use when starting ANY change (feature, fix, refactor, docs, config), when creating or updating a GitHub issue, branch, commit, or pull request, and before pushing or merging to main.
---

# GitHub workflow (issues → branches → PRs → main)

This skill is the operational procedure for the rules in `agent.md` §8 and §10.
**No change of any kind happens outside this workflow** — not a typo fix, not a config tweak, not a docs edit.

## 0. Preconditions (check once per session)

> **yoyo mode:** steps 4–6 (docs → code → tests) run without asking the owner anything — they are not at the device. All questions belong in Planning/Issue (before the branch) and in the review at the end. Never ask mid-implementation.

```cmd
git branch --show-current
gh auth status
```

- Never work on `main`. If on `main`, create a branch first.
- If the repo has uncommitted work from a previous issue, stop and ask the owner before mixing it with new work.

## 1. Branch model

| Branch | Purpose | Rules |
|---|---|---|
| `main` | Always releasable, always green | No direct commits. No force-push. Merge only via reviewed PR. |
| `dev/<issue-number>-<kebab-slug>` | One branch per issue | Created from `main`, deleted after merge |

Naming: lowercase, hyphens, issue number first — **confirmed format**: `dev/<issue-number>-<kebab-slug>`.
`dev/12-login-screen`, `dev/34-fix-dio-timeout`

```cmd
git switch main
git pull
git switch -c dev/12-login-screen
```

- The branch **must** contain the issue number — that is how branch ↔ issue linking works.
- Keep the branch small: one issue = one shippable slice. A branch that no longer matches its issue means the issue was too big → split it (see §3).

## 2. Issue first, always

An issue exists **before** any code. Read `references/issue-template.md` and fill every section — an issue without acceptance criteria is not ready to work on.

```cmd
gh issue create --title "feat(auth): login screen with JWT" --body-file issue.md
```

Rules:
- Title follows Conventional Commits style: `feat(scope): ...`, `fix(scope): ...`, `docs: ...`, `chore: ...`.
- Body must contain: context/why, goal, acceptance criteria (testable), task checklist, affected areas (backend / mobile / docs), test plan, out of scope, docs to update, references.
- Attach labels where available (`backend`, `mobile`, `docs`, `bug`, `feature`).
- If the request from the owner is vague, **ask** — do not invent acceptance criteria.

## 3. Split big work

If the issue cannot be finished and reviewed in one sitting, or touches more than one layer in a non-trivial way:

1. Create an **epic** issue: `feat(<area>): <big feature>` with the full picture.
2. Create small child issues, each independently shippable and testable.
3. Each child issue body starts with `Part of #<epic>`.
4. The epic gets a task list of child issues (`- [ ] #13`, `- [ ] #14`).
5. Each child gets its **own** branch and **own** PR, merged separately.

Never open one giant PR for a multi-part feature.

## 4. Link issue ↔ branch ↔ PR

Linking is mandatory in both directions:

1. Branch name carries the issue number (`dev/12-...`).
2. PR body ends with the closing keyword:
   `Closes #12` (or `Part of #12` for child branches).
3. The issue gets a comment/update with the branch name and the PR link as soon as the PR opens.
4. PR title mirrors the issue title.

```cmd
gh pr create --draft --title "feat(auth): login screen with JWT" --body-file pr.md --base main
```

## 5. Commits

- Conventional Commits, imperative mood, one logical change per commit.
  `feat(auth): add jwt login endpoint`
  `test(auth): cover wrong-password case`
  `docs(api): document /api/v1/auth/login`
- Footer references the issue: `Refs #12`.
- Never commit: `.env`, keys, `.venv/`, build output, `mobile/build/`, IDE files.
- Never `git push --force` on `main` or on a branch someone else may have pulled.

## 6. Push and merge gates (hard stops)

- **Do not push** until the owner confirms the review (see `agent.md` §10 step 7).
- Push to the **PR branch only** — never to `main`.
- Merge to `main` only when: tests pass, coverage ≥ 50%, docs updated, review done, owner approved.
- **The agent performs the merge** after the owner's approval (owner decision). Default: squash merge + delete branch.
- After merge: confirm the issue is closed by the PR, update `docs/` status pages if needed.

```cmd
git add -A
git commit -m "feat(auth): add jwt login endpoint" -m "Refs #12"
git push -u origin dev/12-login-screen
gh pr merge --squash --delete-branch
```

## 7. Checklist before asking for review

- [ ] Issue exists, is filled, and matches what was built
- [ ] Branch named `dev/<n>-<slug>` and based on latest `main`
- [ ] PR is linked to the issue (`Closes #<n>`)
- [ ] Documentation updated in the same PR (`docs/`)
- [ ] Backend: `python -m pytest --cov` passes, coverage ≥ 50%
- [ ] Mobile: `flutter analyze` clean, `flutter test --coverage` passes, coverage ≥ 50%
- [ ] No secrets, no debug leftovers, no commented-out code
- [ ] PR body summarises changes, test evidence, and docs touched

## 8. Anti-patterns

- Committing straight to `main` "because it's small".
- A branch without an issue, or an issue without a branch.
- PR with no description, or description that does not say how it was tested.
- Closing an issue manually while its PR is still open (or vice versa).
- Force-pushing a shared branch to hide messy history instead of squashing on merge.
