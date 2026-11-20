---
name: project-docs
description: Maintain the docs/ documentation set (Laravel-style, multi-file) so that any developer or AI agent can understand and run this project. Use whenever code, schema, API, config, or process changes — and when onboarding, planning, or answering "how does this project work".
---

# Project documentation (docs/)

Two files govern this repo:

| File | Question it answers |
|---|---|
| `agent.md` | **How we work** (rules, stack, workflow, process) |
| `docs/` | **What the project is and how it works** |

Both are part of "done". A change that leaves `docs/` stale is unfinished, no exceptions.

## 1. Two audiences, one bar

Every page must be usable by:

1. **A new human developer** — can clone, run, change the code without asking anyone.
2. **An AI agent** — can read the docs and act correctly without guessing, including paths, commands, and conventions.

That means: explicit paths, exact `cmd` commands, real code samples from this repo, no "see the code for details", no undocumented behaviour.

## 2. Layout (confirmed by owner — see docs-map.md)

Docs live in `docs/`, split by topic — never one giant file. Each file covers one subject, like the Laravel documentation (Installation, Architecture, Routing, Database, Testing, …).

`docs/README.md` is the index: a short map of every page with one line each, plus the "read in this order" path for a newcomer.

`docs/decisions/` holds ADRs: `ADR-0001-<decision>.md` for choices that are expensive to reverse (ORM, auth scheme, model choice, folder layout).

## 3. When to update docs

Update `docs/` in the **same PR** as the change when you:

- add/rename/remove an endpoint, table, column, model, or module
- add/change a config variable or `.env` key
- add/change a mobile screen, BLoC, route, or local table
- change how to install, run, test, or deploy
- make an architectural decision (also add an ADR)
- change a workflow rule (that goes in `agent.md` **and** its `docs/` page if documented there)

If nothing above applies, say so explicitly in the PR — silence is not an option.

## 4. Page rules

- One topic per page; a page that needs a table of contents split in two.
- Start each page with: **What it is → Why it exists → How to use it**.
- Every command block is `cmd` syntax and copy-paste runnable.
- Every code sample is real and current (copied from the repo, trimmed).
- Use relative links between pages; keep the index in sync.
- Document the *why* for non-obvious decisions; document the *how* for everything procedural.
- No screenshots of text — text beats images (an agent cannot read a screenshot reliably).
- No secrets, tokens, keys, or personal data in docs.
- Keep a `docs/status.md` with the current state (what works, what is in progress, what is missing).

## 5. Traceability

- Every doc page may list the related issues/PRs at the bottom (`Related: #12, #14`).
- Every issue lists the docs it makes stale (see the issue template).
- `docs/changelog.md` records user-visible changes with issue links, newest first.

## 6. Procedure when picked up

1. Read `docs/README.md` and `docs/status.md` first.
2. Identify which pages the current task touches (issue's "Documentation to update").
3. Write/update the docs **as part of the implementation**, before review.
4. Re-read the page as if you were the newcomer: can you run the project from it alone?
5. Update `docs/README.md` if pages were added/renamed, and `docs/status.md` if scope changed.

## 7. Anti-patterns

- A single `README.md` pretending to be the documentation.
- Docs describing an old design after a refactor.
- "TODO: document later".
- Business logic explained only in commit messages.
