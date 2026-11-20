# Backend — services and repositories

## What it is

The backend uses a one-way layered flow: route/Jinja view → service → repository → SQLite.
Repositories are the only layer that touches SQLAlchemy; services own rules and transactions.

## Why it exists

This keeps HTTP parsing out of business logic and keeps database access testable. It also makes
ownership checks and factor snapshots consistent across the API and the admin panel.

## How it works

| Layer | Owns | Must not |
|---|---|---|
| Route / Jinja view | parse input, call service, build response/template | write SQL, compute emissions |
| Service | validation, permissions, calculations, transactions, audit | build HTTP responses |
| Repository | queries, eager loading, pagination | commit/rollback |
| Model | columns/relations | business rules |

Example: `records/service.py`

1. Validate category/factor/unit.
2. Load the active factor.
3. Compute `emissions_grams = round(quantity × factor_grams_co2e)`.
4. Snapshot factor value/source/year.
5. Create the record, commit.
6. Return the record + formula breakdown.

Cross-module access goes through public service functions, not another module’s repository.

## How to use it

When adding a feature:

1. Add the model + migration.
2. Add a repository with the queries.
3. Add a service with rules/transactions.
4. Add a route that validates with pydantic and calls the service.
5. Add tests at the service/repository/API levels.

## Testing

- Repositories: temp SQLite, real queries.
- Services: fake/mocked repositories or temp DB; assert rules and errors.
- Routes: Flask test client; assert envelope, status, ownership.

## Related

- Pages: [app factory](app-factory.md), [database](database.md), [api](api.md)
