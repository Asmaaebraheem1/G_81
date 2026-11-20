# 07 — AI sustainability assistant

## Purpose

Give users a grounded chat advisor that answers questions about their calculated footprint,
reports, energy, transport, water, waste, and sustainable habits — without inventing numbers.

## UI (Flutter)

| Screen | Elements |
|---|---|
| `AssistantPage` | message list, user/assistant bubbles, suggested prompts, input, send, context chip |
| `ConversationList` | past conversations, delete, empty/loading |
| `AiStatusBanner` | enabled/disabled/model/vision best-effort |
| `FlagResponseSheet` | reason + notes + submit |

States: initial, loading (typing), success, empty conversation, disabled, rate limited, network
error, flagged, reported, deleted.

## Screen logic (BLoC)

`AssistantBloc`
- Events: `AssistantStarted`, `AssistantMessageSent`, `AssistantConversationOpened`,
  `AssistantConversationDeleted`, `AssistantResponseFlagged`.
- States: `AssistantInitial`, `AssistantLoading`, `AssistantConversationsLoaded`,
  `AssistantSending`, `AssistantSuccess(messages)`, `AssistantDisabled`,
  `AssistantRateLimited`, `AssistantFailure(message)`.

The UI shows a persistent badge: “AI explanation — calculated values come from CarbonWise.” It
never renders AI text as a calculated total.

## Backend logic

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/v1/ai/status` | JWT | enabled/model/vision |
| POST | `/api/v1/ai/chat` | JWT | grounded answer |
| GET | `/api/v1/ai/conversations` | JWT | list |
| GET | `/api/v1/ai/conversations/{id}` | JWT | messages |
| DELETE | `/api/v1/ai/conversations/{id}` | JWT | delete |
| POST | `/api/v1/ai/flag` | JWT | report a response |

Rules:
- Build context from calculated data only; no other users, no raw DB access.
- Trim history to the last N messages; cap tokens.
- Rate limit/budget/cache; record `ai_usage` metadata; no prompt logs.
- Empty content → `ai_empty_response`; disabled → `ai_disabled`; 429 → `rate_limited`.
- If no key, return a calculated fallback card (top categories) labelled as fallback, not AI.
- Store conversation/messages for history; user can delete.
- Flagged responses are redacted before admin review.

## Data

Tables: `ai_conversations`, `ai_messages`, `ai_usage`, `ai_cache`, `ai_flagged_responses`.
Invariants: user-scoped; no raw prompts in logs; model recorded; no AI number authority.

## Acceptance criteria

1. A user can start a conversation, send a message, and receive a grounded answer.
2. The response includes a disclaimer and a calculated context block.
3. AI is disabled gracefully without a key; a fallback is shown and labelled.
4. 429/outage/empty content produce typed, friendly errors.
5. Conversations persist and can be deleted.
6. A user can report a response; the flag is stored for admin review.
7. A user cannot read another user’s conversation.
8. EN/AR prompts/responses and RTL bubbles work.
9. No tokens/keys/prompts appear in logs or usage rows.

## Tests

| Type | File | Covers |
|---|---|---|
| Service | `tests/modules/ai/test_assistant.py` | context, history trim, fallback, flags |
| API | `tests/api/test_ai_chat.py` | success, disabled, 429, ownership |
| AI mock | `tests/fakes/openrouter.py` | text, empty, timeout |
| Mobile BLoC | `test/features/assistant/assistant_bloc_test.dart` | send/success/disabled/failure |
| Widget | `test/features/assistant/assistant_page_test.dart` | bubbles, disclaimer, EN/AR |

## Status

🟡 in progress — issue #18.

Related: #18
