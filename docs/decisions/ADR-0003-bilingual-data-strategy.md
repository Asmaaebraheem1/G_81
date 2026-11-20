# ADR-0003 — Bilingual data strategy (EN + AR)

- **Status:** accepted
- **Date:** 2026-11-19
- **Deciders:** owner + agent

## Context

The app must support English and Arabic (RTL) from day one. User-facing content includes
categories, factors, alternatives, challenges, badges, notifications, articles, and AI text.
The admin must edit both languages.

## Decision

- App UI strings live in ARB files (`app_en.arb`, `app_ar.arb`) and are generated with
  `flutter gen-l10n`.
- Persistent user-facing domain content uses explicit `*_en` and `*_ar` columns.
- AI responses are requested in the user’s locale and stored with a `locale` field; AI-generated
  plan/alternative text is not machine-translated after generation.
- The admin UI is English in v1; forms expose both language fields.
- RTL is verified on every screen and screenshot.

## Consequences

### Positive
- No runtime translation service or extra provider.
- Admin can correct translations.
- The seed is fully bilingual.

### Negative / trade-offs
- Every content model/form needs two fields.
- AI quality in Arabic depends on the routed free model.
- More strings to maintain.

### Follow-ups
- Lint for hardcoded user-facing strings.
- Screenshot coverage includes EN and AR for every mobile screen.

## Alternatives considered

| Alternative | Why not |
|---|---|
| Runtime translation API | New dependency, cost, quality risk |
| English-only content | Violates the bilingual requirement |
| JSON translation blobs | Harder to query/validate than columns |

Related: #3, #4
