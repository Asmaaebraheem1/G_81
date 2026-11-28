# Reports

## Arabic project report (Word)

[`CarbonWise-Project-Report-AR.docx`](CarbonWise-Project-Report-AR.docx) is the
standalone Arabic RTL report for presentation and submission. It explains the
project idea, problem, users, journeys, F01–F15 features, system behaviour, the
five diagrams, the full technology stack (what each tool is used for), the AI
guardrails, data model, security, test evidence, demo access, deliverables and
known limits.

**Open it in Microsoft Word** (or LibreOffice) and update the table of contents
with `F9` if Word does not refresh fields automatically on open. The document is
editable; it is a deliverable, not a build artefact.

## Project-idea sheet (G_81)

[`G_81-Project-Idea-AR.docx`](G_81-Project-Idea-AR.docx) is the short two-page
Arabic RTL summary:

- **Page 1** — the project idea in one paragraph of roughly half a page.
- **Page 2** — the names of the technologies used, with no descriptions.

The project number `G_81` is part of the file name and appears at the top of
both pages.

## Source of truth

Both documents are derived from the v1.0.0 repository state:

- `docs/status.md`, `docs/05-data-model.md`, `docs/06-api-reference.md`
- `docs/ai-features.md`, `docs/00-overview.md`, `docs/features/`
- `backend/requirements.txt`, `mobile/pubspec.yaml`
- the five diagrams in `docs/diagrams/` and the screenshot library

If a fact changes (routes, tables, test counts, versions), update the report in
the same change. Do not add invented screenshots, test results or AI claims.

## Generation notes

Both DOCX files are generated with `python-docx` in the local backend venv. That
package is developer tooling, **not** a runtime or CI dependency; the committed
Word files are the deliverables.

```cmd
cd /d D:\projects_is_2026\G_81
backend\.venv\Scripts\pip.exe install python-docx==1.2.0

backend\.venv\Scripts\python.exe docs\reports\build_report.py
backend\.venv\Scripts\python.exe docs\reports\build_project_idea.py
```

`build_report.py` also uses `Pillow` (already required by the diagram/asset
scripts) and `lxml` (installed with `python-docx`). It embeds the diagrams and
screenshots. `build_project_idea.py` is text-only and produces exactly two
pages. Both write their DOCX in place.

Validate either file in Word before committing; the report's table of contents is
a field and is refreshed on open (or with `F9`).

Related: #24, #26
