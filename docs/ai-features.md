# AI features — contract, models, and limitations

## Policy

- Provider: **OpenRouter**, backend only (`backend/app/modules/ai`).
- Model: **`openrouter/free`** only. It is OpenRouter’s free model router; the actual model
  returned by OpenRouter is recorded in `ai_usage.model` and on generated content.
- **No paid fallback, no alternative provider, no independent model training or fine-tuning.**
- The Flutter app never holds the API key and never calls OpenRouter directly.
- Every AI call is mocked in tests; `TestingConfig` blanks `OPENROUTER_API_KEY`.
- AI output is **never** the source of an emission value, a factor, a percentage reduction, or an
  estimated saving. Those come from backend calculations and documented assumptions.
- The AI is an explainer, summarizer, planner, and recommender — not a calculator and not a
  database writer.

## Capability matrix

| Feature | Endpoint | Input modality | Output | Model |
|---|---|---|---|---|
| Sustainability assistant | `POST /api/v1/ai/chat` | text + server context | text | `openrouter/free` |
| Report insights | `POST /api/v1/ai/insights` | text + server context | validated JSON + narrative | `openrouter/free` |
| Sustainability summary | `POST /api/v1/ai/summary` | text + server context | text | `openrouter/free` |
| Reduction plan | `POST /api/v1/plans/generate` | text + server context | validated JSON plan | `openrouter/free` |
| Personalized alternatives | `GET /api/v1/alternatives/recommended` | text + server context + catalog | selected IDs + rationale | `openrouter/free` |
| Bill/receipt extraction | `POST /api/v1/documents/{id}/extract` | image + text instruction | validated JSON fields | `openrouter/free`, **best effort vision** |

`openrouter/free` may route to a different free model per request. The app must not promise OCR
or a specific model. If the routed model rejects image input, the backend returns
`vision_unavailable` and the app falls back to manual entry.

## Server-built context

The backend builds a compact JSON context from **calculated data only**:

- period and timezone
- total emissions (grams and kg)
- category totals and shares
- previous-period totals and change %
- top activities (category + quantity + factor + emissions)
- active goals (baseline, target, progress)
- active/recent plan actions (if any)
- user locale and account type
- for alternatives: the catalog IDs and documented assumptions
- for extraction: the image only + a strict instruction; no unrelated personal data

The model never receives database credentials, other users’ data, raw prompt logs, or secrets.

## Output validation

- Chat/summary: plain text; reject empty content (`ai_empty_response`).
- Insights: JSON schema
  `{ top_sources: [...], changes: [...], comparisons: [...], opportunities: [...], narrative: str }`.
- Plan: JSON schema
  `{ title: str, summary: str, actions: [{ title, description, category_key, priority,
  timeframe, estimated_saving_percent? }] }`. The backend maps `category_key` to a real category,
  calculates any estimated saving from documented assumptions, and rejects unknown keys.
- Alternatives: JSON `{ selected_ids: [int], rationale: str }`; backend validates IDs against the
  active catalog and computes impact.
- Extraction: JSON `{ vendor?, billing_period?, consumption_value?, unit?, confidence? }`; backend
  validates types/ranges and never saves without user confirmation.

Malformed output → one retry with the same model → typed error and graceful UI fallback.

## Prompting rules

- System prompt states: “Use only the provided calculated values. Do not invent emission values,
  factors, savings, or sources. If a value is missing, say so.”
- The system prompt asks for the user’s locale (EN/AR) and a concise, practical answer.
- The backend injects a disclaimer and a `calculated_context` block in the response envelope.
- No prompt contains a user’s email, phone, full name, token, or raw document text.
- The app labels AI content with an “AI-generated explanation” badge and separates it from
  “Calculated by CarbonWise” cards.

## Lifecycle, limits, and fallbacks

| Concern | Rule |
|---|---|
| Completion budget | floor 4096 tokens; hidden reasoning capped at 1024 |
| Daily budget | `AI_DAILY_TOKEN_BUDGET` (default 200,000) |
| Rate limit | `AI_RATE_LIMIT_PER_HOUR` (default 20 per user) |
| Cache | prompt-hash cache scoped per user/context, TTL default 60 min |
| Retries | at most 2 on 429/5xx with backoff; no infinite retries |
| Timeout | 45 seconds |
| Disabled | no key → `503 ai_disabled`; calculated/rules fallback shown |
| Empty content | typed `ai_empty_response`; no “None” text |
| Vision unavailable | `422 vision_unavailable` → manual entry |
| Invalid structured output | one retry → `502 ai_invalid_output` → template fallback |
| Rate limited | `429 rate_limited` with a friendly message |
| Outage | friendly error + calculated fallback; usage recorded as error |

Rules/template fallbacks never claim to be AI. They are labelled “Calculated fallback” or
“Curated alternative”.

## Privacy and consent

- Before sending a bill image, the app shows: “This image will be sent to OpenRouter’s free model
  for extraction. Free models may have different data-retention policies. You can enter the values
  manually instead.”
- Consent is required (`consent=true`); without it, extraction is not attempted.
- `ai_usage` stores metadata only: feature, actual model, token counts, latency, status, request
  hash. No raw prompts.
- `ai_messages` stores conversation content so the user can see history; it is user-scoped and
  deletable.
- Reported responses (`ai_flagged_responses`) may store the response text after PII redaction for
  admin review; admin UI shows a privacy warning.
- No AI data is used for model training by this project.

## Feature details

### 1. Sustainability assistant

- Purpose: answer questions about the user’s footprint, reports, energy, transport, water, waste,
  and sustainable habits.
- Input: message + conversation history (trimmed) + calculated context.
- Output: concise text with practical suggestions and, when relevant, a reference to the user’s
  calculated totals/categories.
- Limitations: no real-time grid data; no professional/legal advice; uses only recorded data.
- UI: chat bubbles, suggested prompts, “calculated context” chip, report/flag action.

### 2. Emission insights

- Purpose: identify top sources, unusual changes, category comparisons, and opportunities.
- Input: period, totals, category shares, previous-period comparison, top activities.
- Output: validated structured insights + narrative.
- Limitations: anomalies are based on recorded data; insufficient data is stated explicitly.
- UI: insight cards, “Calculated” vs “AI explanation” labels, refresh.

### 3. Sustainability summary

- Purpose: plain-language summary of a period for the user or export.
- Input: calculated period summary.
- Output: short narrative; no new numbers.
- UI: report summary card; copy button.

### 4. Reduction plan

- Purpose: turn a goal and top categories into a practical, prioritized plan.
- Input: goal baseline/target, top categories, recent records, locale, constraints.
- Output: validated actions with priority/timeframe; estimated savings calculated by the backend
  from category emissions × documented action assumption.
- Limitations: estimated savings are estimates, not guarantees; plan actions are suggestions.
- UI: plan timeline, action checkboxes, “estimated saving” chip with assumption link.

### 5. Personalized alternatives

- Purpose: recommend lower-emission alternatives from a curated catalog.
- Input: user patterns, top categories, catalog IDs + assumptions.
- Output: selected IDs + rationale; backend validates and computes impact.
- Limitations: catalog coverage; AI may omit an alternative; no invented IDs.
- UI: alternative cards with estimated impact and assumption text.

### 6. Bill/receipt extraction

- Purpose: reduce manual entry by reading visible values from an uploaded image.
- Input: image + strict extraction instruction.
- Output: candidate JSON fields + confidence.
- Limitations: best-effort; handwriting/low quality may fail; PDF is not extracted in v1; the user
  must confirm; no automatic save.
- UI: upload → consent → extracting → editable confirmation → save record.

## Monitoring (admin)

`/admin/ai` shows: total calls, tokens, status mix, model distribution, failures, recent usage,
flagged responses, budget usage, and the fixed model policy. It never shows raw prompts. Admins
can review a reported response, add notes, and mark it reviewed/dismissed. The model setting is
read-only (`openrouter/free`); changing it would violate the stack.

## Testing

- `tests/modules/ai/test_client.py`: mocked httpx responses, 429/5xx, empty content, malformed JSON.
- `tests/modules/ai/test_services.py`: budget, rate limit, cache, context building, validation.
- API tests: `ai_disabled`, `vision_unavailable`, `rate_limited`, happy path.
- No real network calls; no key required.
- Mobile tests: BLoC states for success/failure/disabled; no real Dio call.

Related: #8, #11, #18
