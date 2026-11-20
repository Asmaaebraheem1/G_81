# ADR-0004 — Private filesystem uploads with authenticated download

- **Status:** accepted
- **Date:** 2026-11-19
- **Deciders:** owner + agent

## Context

The app stores electricity bills and fuel receipts, which contain personal and financial data.
The template default (`backend/app/static/uploads/`) is web-served and therefore risky. The stack
allows local filesystem storage and forbids cloud storage.

## Decision

Store uploads privately under `backend/instance/uploads/` (git-ignored), with generated filenames.
Serve them only through authenticated API/admin routes that check ownership/role. Validate content
type by magic bytes, enforce size limits, strip unsafe metadata where feasible, and never execute
files. PDFs are stored but not AI-extracted in v1.

## Consequences

### Positive
- Bills are not publicly reachable by guessing a URL.
- No cloud dependency or secrets.
- Tests can use `tmp_path`.

### Negative / trade-offs
- The app must proxy downloads instead of using a static URL.
- Local demo backup is manual.
- Metadata stripping requires Pillow for images.

### Follow-ups
- Add an admin download audit if needed.
- Document retention/deletion behavior.

## Alternatives considered

| Alternative | Why not |
|---|---|
| Public `static/uploads` | Leaks bills/receipts |
| Cloud object storage | Forbidden by the stack |
| Database BLOBs | Bloats SQLite, harder streaming |

Related: #8
