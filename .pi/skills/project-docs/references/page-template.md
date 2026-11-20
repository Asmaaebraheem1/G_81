# Doc page template

Copy this skeleton into any new `docs/` page.

```markdown
# <Page title>

## What it is
One short paragraph. What this part of the system does.

## Why it exists
The problem it solves, and the constraints that shaped it (link ADRs).

## How it works
- Key files and paths (real ones):
  - `backend/app/modules/<x>/services.py`
- Flow / sequence (text or mermaid)
- Important invariants and gotchas

## How to use it
Step-by-step, `cmd` syntax, copy-paste runnable.

## Configuration
| Key | Default | Meaning |
|---|---|---|
| `OPENROUTER_MODEL` | `openrouter/free` | ... |

## Testing
How this part is tested and which files prove it.

## Related
- Issues: #12
- ADRs: ADR-0001
- Pages: [architecture](../04-architecture.md)
```

## Checklist for a page

- [ ] Path and command examples match the repo exactly
- [ ] An agent could act on this page without reading the code
- [ ] Linked from `docs/README.md`
- [ ] No secrets, no stale screenshots
- [ ] `docs/status.md` reflects the truth about this area
