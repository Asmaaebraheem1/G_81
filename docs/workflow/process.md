# Workflow

The normative rules are in [`agent.md`](../../agent.md) §8–§10. This page is the practical version.

## Branches

| Branch | Rule |
|---|---|
| `main` | always green, no direct commits, no force-push |
| `dev/<issue>-<slug>` | one per issue, from `main`, deleted after merge |

```cmd
git switch main
git pull
git switch -c dev/12-login-screen
```

## The 9 steps

| # | Step | Mode | Output |
|---|---|---|---|
| 1 | Planning | with owner | files, risks, questions |
| 2 | Issue | with owner | complete issue |
| 3 | Branch + draft PR | with owner | linked draft PR |
| 4 | Documentation | **yoyo** | docs updated |
| 5 | Coding | **yoyo** | implementation |
| 6 | Testing | **yoyo** | tests + coverage ≥ 50% |
| 7 | Review | with owner | report + confirmation |
| 8 | Push | after confirm | commits on the PR branch |
| 9 | Merge | agent, when green | squash + delete branch |

## Commands

```cmd
git add -A
git commit -m "feat(auth): add jwt login endpoint" -m "Refs #12"
git push -u origin dev/12-login-screen
gh pr create --draft --title "feat(auth): login screen with JWT" --body-file "%TEMP%\pr.md" --base main
gh pr ready
gh pr merge --squash --delete-branch
git switch main
git pull
```

## Gates

- No push before review confirmation (unless yoyo is explicitly on).
- Merge only with green CI, docs updated, coverage ≥ 50%.
- After merge: issue closed by `Closes #n`; changelog/status updated.

## Recovery

```cmd
git fetch --prune origin
git reset --hard origin/main
```

Use only when local `main` is stale or a ref-lock blocks the merge; never on a branch with
unpushed work.
