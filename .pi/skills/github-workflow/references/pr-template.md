# Pull request template

## Title
Same as the issue title: `<type>(<scope>): <summary>`

## What changed
Bullet list of concrete changes, grouped by layer (backend / mobile / docs).

## Why
One paragraph, link the issue: `Closes #<n>` (or `Part of #<n>`).

## How it was tested
- Commands run (cmd syntax) and their result:
  - `python -m pytest --cov`
  - `flutter analyze`
  - `flutter test --coverage`
- Coverage: backend __% / mobile __%
- Manual steps verified:

## Screenshots / evidence
Admin panel pages, app screens, or API responses (redact tokens/secrets).

## Documentation
Which `docs/` pages were created or updated.

## Risks / notes
Migrations, breaking changes, follow-up issues.

## Checklist
- [ ] Linked to an issue
- [ ] Tests added/updated for every acceptance criterion
- [ ] Coverage ≥ 50% on both sides
- [ ] Docs updated in this PR
- [ ] No secrets, no debug code, no dead code
- [ ] `main` is not the source branch
