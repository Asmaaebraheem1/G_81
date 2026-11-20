# ADR-0002 — OpenRouter `openrouter/free` only; best-effort vision

- **Status:** accepted
- **Date:** 2026-11-19
- **Deciders:** owner + agent

## Context

The idea asks for suitable language and multimodal models through OpenRouter. The fixed stack
requires the free router `openrouter/free` only, no paid fallback, and a backend-only key.
Free routing can change the actual model per request, so vision cannot be guaranteed.

## Decision

Use `openrouter/free` exclusively through the backend. Record the actual model returned. Treat
image extraction as best-effort: if the routed model does not support images, return
`vision_unavailable` and fall back to manual entry. Never use a paid model or a second provider.
All AI calls are mocked in tests and budgeted/rate-limited/cached in production.

## Consequences

### Positive
- No AI spend; one provider and one model constant.
- The app cannot silently switch to a paid model.
- Clear UI fallback when vision is unavailable.

### Negative / trade-offs
- Vision quality and availability vary.
- Free-model data policies may differ; consent is required before image upload.
- The actual model name is dynamic and must be monitored.

### Follow-ups
- Document the model capability caveat in `docs/ai-features.md` and the UI consent notice.
- Monitor failures in `/admin/ai`.
- Keep prompts strict about not inventing numbers.

## Alternatives considered

| Alternative | Why not |
|---|---|
| A specific paid vision model | Violates the fixed stack and budget |
| Multiple free model IDs | The stack fixes `openrouter/free` |
| Local OCR/model training | Unnecessary; violates “no independent training” |
| No AI extraction | Allowed fallback, but the idea requests document analysis |

Related: #8, #18
