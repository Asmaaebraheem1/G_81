# System analysis diagrams

## Required set

| # | Diagram | File | Editable source |
|---|---|---|---|
| 1 | Context Diagram | `01-context.png` | `generate_diagrams.py` |
| 2 | DFD — Level 0 | `02-dfd-level-0.png` | `generate_diagrams.py` |
| 3 | DFD — Level 1 | `03-dfd-level-1.png` | `generate_diagrams.py` |
| 4 | Use Case Diagram | `04-use-case.png` | `generate_diagrams.py` |
| 5 | Entity Relationship Diagram | `05-erd.png` | `generate_diagrams.py` |

All five PNGs are produced by the single editable Python source in this folder. The
generator is deterministic, uses only Pillow and Windows system fonts, and writes
300 DPI PNGs. No PlantUML/Graphviz installation is required.

## Design rules

- **Strictly black and white.** White background, black strokes and text only. No
  colours, fills, gradients, shadows, or decorative effects.
- Clear, professional, properly structured, readable at 100% and printable.
- Each diagram is a separate high-quality PNG (300 DPI) plus the editable source.
- Consistent naming, header, footer, and layout.
- The ERD matches `docs/05-data-model.md` and includes all 29 v1 tables.
- The use case diagram covers guest, individual/household user, organization user,
  admin/content editor, and the external OpenRouter system.
- DFD Level 1 shows auth/profile, catalog, records/calculation, documents, reports,
  goals/plans, engagement, AI, and admin, with data stores D1–D7.

## Generate

From the repository root:

```cmd
backend\.venv\Scripts\python.exe docs\diagrams\generate_diagrams.py
```

or through the convenience wrapper:

```cmd
backend\.venv\Scripts\python.exe scripts\generate_diagrams.py
```

Requirements: Python 3.11+ and Pillow (already in `backend/requirements-dev.txt`).
Fonts are read from `C:\Windows\Fonts\arial.ttf` and `arialbd.ttf`; change `FONT_REGULAR`
and `FONT_BOLD` in the generator when running on another platform.

## Layout notes

- **Context / DFD-0:** the platform is one boundary; external entities are the
  individual/household user, organization user, admin/content editor, and OpenRouter.
  Two-way flows are drawn as separate arrows so direction is explicit.
- **DFD-1:** nine processes in a 3×3 grid, seven data stores D1–D7 below them, and
  three human actors on the left. Data-store flows are routed through empty lanes so
  they do not cross process boxes. The bottom note records the flows that would
  otherwise add long crossing lines (`5.0 reads D3`; `9.0 edits D2/D7`) and restates
  that process 3.0 owns emission calculation and factor snapshots.
- **Use case:** one boundary, actors outside. Umbrella use cases keep the diagram
  legible while the linked feature pages (`docs/features/`) enumerate every sub-case.
  OpenRouter is an external actor participating only in the assistant/insights use case.
- **ERD:** six domain columns and five rows of entity boxes, with all 29 tables and
  their key attributes. Connectors are drawn behind the boxes; the key-relationship
  panel lists cardinalities that would otherwise require long crossing lines.

## Verification

- Images are pure black/white (RGB channels equal) apart from antialiasing.
- Every file opens and is readable at 100% and in print preview.
- The editable source is committed beside the PNGs.
- `docs/screenshots/README.md` and `docs/README.md` link this page.
