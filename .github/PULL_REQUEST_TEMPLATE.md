## Summary

<!-- What changed and why. Link the issue. -->

Closes #

## Scope

- [ ] Backend (`/api/v1`, services, models, migrations)
- [ ] Admin (`/admin`, Jinja, CSRF, audit)
- [ ] Mobile (Flutter, BLoC, EN/AR)
- [ ] Docs / diagrams / screenshots / assets
- [ ] CI / scripts

## Verification

```text
# paste the commands you ran and their result
```

- [ ] `ruff check` and `black --check` pass (backend)
- [ ] `pytest --cov=app --cov-fail-under=50` passes
- [ ] `flutter analyze` has 0 errors
- [ ] `flutter test --coverage` passes; `scripts/check_lcov.py` gate passes
- [ ] L10n parity checked (`mobile/tool/check_l10n.py`)
- [ ] Screenshots/docs updated, or a reason is recorded

## Rules checklist

- [ ] One issue, one branch (`dev/<n>-<slug>`), one PR
- [ ] No push to `main`
- [ ] `/api/v1` (JSON + JWT) and `/admin` (Jinja + cookie + CSRF) are not mixed
- [ ] AI never invents emission values; calculations stay in the backend
- [ ] No secrets, tokens, or real bill data in the diff
