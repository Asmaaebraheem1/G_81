# 04 — Bill/document uploads & AI extraction

## Purpose

Let users attach an electricity bill or fuel receipt, extract candidate values with the free
OpenRouter model when it supports images, and confirm/correct them before the backend calculates
and saves a record.

## UI (Flutter)

| Screen | Elements |
|---|---|
| `DocumentsPage` | list with status chips, empty/loading/error, delete unlinked |
| `UploadDocumentPage` | camera/gallery/file picker, file preview, size/type hint, consent checkbox, upload progress |
| `ExtractionReviewPage` | extracted fields editable, confidence badge, category/factor picker, confirm/cancel, manual-entry fallback |
| `DocumentDetailPage` | metadata, status, linked record, download/open, delete |

States: uploading, extracting, extracted, vision unavailable, failed, confirmed, rejected,
consent missing, too large, unsupported type.

## Screen logic (BLoC)

`DocumentsBloc`
- Events: `DocumentsStarted`, `DocumentUploaded`, `DocumentExtractRequested`,
  `DocumentConfirmed`, `DocumentRejected`, `DocumentDeleted`.
- States: `DocumentsInitial`, `DocumentsLoading`, `DocumentsEmpty`, `DocumentsSuccess(list)`,
  `DocumentsUploading(progress)`, `DocumentsExtracting`, `DocumentsExtracted(fields)`,
  `DocumentsVisionUnavailable`, `DocumentsFailure(message)`.

`DocumentUploadBloc` validates the file locally (size/type) and obtains consent before upload.
`ExtractionConfirmationBloc` validates fields and calls confirm; no automatic save.

## Backend logic

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/v1/documents` | JWT | multipart upload, consent |
| GET | `/api/v1/documents` | JWT | own documents |
| GET | `/api/v1/documents/{id}` | JWT | metadata/status |
| GET | `/api/v1/documents/{id}/download` | JWT | authenticated download |
| POST | `/api/v1/documents/{id}/extract` | JWT | best-effort AI extraction |
| POST | `/api/v1/documents/{id}/confirm` | JWT | validate + create record |
| DELETE | `/api/v1/documents/{id}` | JWT | delete unlinked |

Rules:
- Allowed images: JPEG/PNG/WebP; PDF allowed as an attachment but **not** AI-extracted in v1.
- Validate MIME by content; max 10 MB/file, 30 MB/request.
- Store privately under `instance/uploads/<user_id>/`; generated filename; no execution.
- Extraction does not create a record; it stores candidate JSON + model.
- If `openrouter/free` routes to a non-vision model, return `422 vision_unavailable`.
- Confirmation validates category/factor/quantity/unit/date, creates the record with a snapshot,
  links `document.record_id`, and sets status `confirmed`.
- Ownership checks on every endpoint; admin download is in feature 14.

## Data

Tables: `documents`, `consumption_records` (link), `ai_usage`, `ai_cache`.
Invariants: one document ↔ at most one record; private file; extraction JSON only after consent;
no auto-save; status transitions per `docs/05-data-model.md`.

## Acceptance criteria

1. A user can upload a JPG/PNG/WebP/PDF under the size limits.
2. Oversized/unsupported/mismatched files are rejected with typed errors.
3. The consent checkbox is required before extraction; declining keeps manual entry.
4. Extraction returns editable candidate fields + model/confidence, never a saved record.
5. Vision unavailable returns a typed error and a manual-entry form; the file stays attached.
6. Confirm creates exactly one record, links the document, and shows the formula.
7. A user cannot access another user’s document/file.
8. Deleting an unlinked document removes the row and file; linked documents cannot be deleted.
9. PDFs are stored but not sent to AI.
10. No prompts or image contents are logged.

## Tests

| Type | File | Covers |
|---|---|---|
| Service | `tests/modules/documents/test_services.py` | MIME/size, ownership, confirm, link |
| API | `tests/api/test_documents.py` | upload/extract/confirm/delete, vision error |
| AI mock | `tests/modules/ai/test_vision.py` | success, vision unavailable, malformed fields |
| Mobile BLoC | `test/features/documents/documents_bloc_test.dart` | upload/extract/confirm/failure |
| Widget | `test/features/documents/extraction_review_test.dart` | editable fields, consent, EN/AR |

## Status

🟡 in progress — issue #8.

Related: #8
